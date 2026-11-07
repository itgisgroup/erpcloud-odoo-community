"""A human-reviewed, idempotent path from AI suggestion to a draft quotation."""
import hashlib
import json

from odoo import api, fields, models, Command
from odoo.exceptions import AccessError, ValidationError


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


class MCPProposal(models.Model):
    _name = "erpcloud.mcp.center.proposal"
    _description = "MCP Center Quotation Proposal"
    _order = "create_date desc, id desc"

    requester_id = fields.Many2one("res.users", required=True, index=True, ondelete="restrict")
    approver_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    company_id = fields.Many2one("res.company", required=True, index=True)
    key_id = fields.Many2one("erpcloud.mcp.center.key", ondelete="set null")
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    state = fields.Selection([("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("expired", "Expired")], required=True, default="pending", index=True)
    request_key = fields.Char(required=True, index=True)
    request_hash = fields.Char(required=True)
    inputs_json = fields.Json(required=True)
    preview_json = fields.Json(required=True)
    preview_hash = fields.Char(required=True)
    expires_at = fields.Datetime(required=True)
    sale_order_id = fields.Many2one("sale.order", readonly=True, ondelete="set null")
    decision_at = fields.Datetime(readonly=True)
    decision_note = fields.Char(readonly=True)

    _request_unique = models.Constraint("unique(requester_id, request_key)", "A request key may only be used once per user.")

    @api.model
    def _business_env(self, user, company):
        return self.env["sale.order"].with_user(user).with_company(company).with_context(allowed_company_ids=[company.id])

    @api.model
    def _preview(self, user, company, inputs):
        if not isinstance(inputs, dict):
            raise ValidationError("Dữ liệu báo giá không hợp lệ.")
        try:
            partner_id = int(inputs.get("partner_id"))
            lines = inputs.get("lines")
            if not isinstance(lines, list) or not 1 <= len(lines) <= 20:
                raise ValueError()
            normalized = [(int(line["product_id"]), float(line["quantity"])) for line in lines]
        except (TypeError, ValueError, KeyError, OverflowError) as exc:
            raise ValidationError("Chọn khách hàng và 1–20 dòng sản phẩm hợp lệ.") from exc
        if any(not 0 < qty <= 1000 for _, qty in normalized):
            raise ValidationError("Số lượng phải lớn hơn 0 và không quá 1.000.")
        order_model = self._business_env(user, company)
        order_model.check_access("create")
        partner = self.env["res.partner"].with_user(user).with_company(company).with_context(allowed_company_ids=[company.id]).browse(partner_id).exists()
        if not partner:
            raise ValidationError("Không tìm thấy khách hàng trong phạm vi quyền.")
        partner.check_access("read")
        products = self.env["product.product"].with_user(user).with_company(company).with_context(allowed_company_ids=[company.id]).browse([pid for pid, _ in normalized]).exists()
        if len(products) != len({pid for pid, _ in normalized}):
            raise ValidationError("Có sản phẩm không tồn tại hoặc không được phép xem.")
        products.check_access("read")
        if any(not product.sale_ok or not product.active or (product.company_id and product.company_id != company) for product in products):
            raise ValidationError("Sản phẩm không được phép bán trong công ty này.")
        note = str(inputs.get("note") or "").strip()[:500]
        order = order_model.new({
            "partner_id": partner.id, "company_id": company.id,
            "order_line": [Command.create({"product_id": pid, "product_uom_qty": qty}) for pid, qty in normalized],
        })
        preview_lines = []
        for line in order.order_line:
            preview_lines.append({
                "product_id": line.product_id.id, "product": line.product_id.display_name,
                "quantity": line.product_uom_qty, "unit": line.product_uom_id.name,
                "price_unit": line.price_unit, "tax_ids": line.tax_ids.ids,
                "subtotal": line.price_subtotal, "total": line.price_total,
            })
        return {
            "partner_id": partner.id, "partner": partner.display_name,
            "company_id": company.id, "company": company.name,
            "pricelist_id": order.pricelist_id.id, "currency": order.currency_id.name,
            "note": note, "lines": preview_lines,
            "amount_untaxed": order.amount_untaxed, "amount_tax": order.amount_tax,
            "amount_total": order.amount_total,
        }

    @api.model
    def propose(self, key, inputs, request_key):
        if (not key or not key.active or key.expires_at <= fields.Datetime.now()
                or key.user_id != self.env.user or key.company_id not in self.env.user.company_ids):
            raise AccessError("Connection is not active for this Odoo user and company.")
        if key.scope != "quote":
            raise AccessError("Kết nối này chỉ được xem dữ liệu.")
        request_key = str(request_key or "").strip()
        if not 8 <= len(request_key) <= 128:
            raise ValidationError("Mã yêu cầu phải dài 8–128 ký tự.")
        request_hash = _digest(inputs)
        self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ["mcp-quote:%s:%s" % (key.user_id.id, request_key)])
        existing = self.sudo().search([("requester_id", "=", key.user_id.id), ("request_key", "=", request_key)], limit=1)
        if existing:
            if existing.request_hash != request_hash:
                raise ValidationError("Mã yêu cầu đã dùng cho nội dung khác.")
            return existing
        preview = self._preview(key.user_id, key.company_id, inputs)
        return self.sudo().create({
            "requester_id": key.user_id.id, "company_id": key.company_id.id,
            "key_id": key.id, "partner_id": preview["partner_id"],
            "request_key": request_key, "request_hash": request_hash,
            "inputs_json": inputs, "preview_json": preview,
            "preview_hash": _digest(preview),
            "expires_at": fields.Datetime.add(fields.Datetime.now(), minutes=30),
        })

    def decide(self, approve, note=""):
        self.ensure_one()
        actor = self.env.user
        if not (actor.has_group("erpcloud_mcp_center.group_mcp_center_approver") or actor.has_group("base.group_system")):
            raise AccessError("Bạn cần quyền duyệt báo giá AI.")
        if self.company_id not in actor.company_ids:
            raise AccessError("Báo giá thuộc công ty khác.")
        self.env.cr.execute("SELECT id FROM erpcloud_mcp_center_proposal WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(["state", "expires_at", "sale_order_id"])
        if self.state == "approved" and approve and self.sale_order_id:
            return self.sale_order_id
        if self.state != "pending":
            raise ValidationError("Đề xuất đã được xử lý.")
        if self.expires_at <= fields.Datetime.now():
            self.sudo().write({"state": "expired"})
            raise ValidationError("Đề xuất đã hết hạn; hãy tạo bản xem trước mới.")
        if not approve:
            self.sudo().write({"state": "rejected", "approver_id": actor.id,
                               "decision_at": fields.Datetime.now(), "decision_note": str(note or "")[:250]})
            return self.env["sale.order"]
        current = self._preview(self.requester_id, self.company_id, self.inputs_json)
        if _digest(current) != self.preview_hash:
            raise ValidationError("Giá hoặc dữ liệu đã thay đổi; hãy xem trước lại.")
        lines = [Command.create({
            "product_id": row["product_id"], "product_uom_qty": row["quantity"],
            "price_unit": row["price_unit"], "tax_ids": [Command.set(row["tax_ids"])],
        }) for row in current["lines"]]
        order_model = self._business_env(self.requester_id, self.company_id)
        order = order_model.create({
            "partner_id": current["partner_id"], "company_id": self.company_id.id,
            "pricelist_id": current["pricelist_id"], "order_line": lines,
            "note": current["note"],
        })
        if order.state != "draft" or order.currency_id.name != current["currency"] or abs(order.amount_total - current["amount_total"]) > order.currency_id.rounding:
            raise ValidationError("Báo giá tạo ra khác bản xem trước; giao dịch đã được hủy.")
        self.sudo().write({"state": "approved", "approver_id": actor.id,
                           "decision_at": fields.Datetime.now(), "sale_order_id": order.id})
        return order
