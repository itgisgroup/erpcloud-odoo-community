"""Named, scoped credentials for a real Odoo user."""
import hashlib
import secrets

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class MCPKey(models.Model):
    _name = "erpcloud.mcp.center.key"
    _description = "MCP Center Connection Key"
    _order = "create_date desc, id desc"

    name = fields.Char(required=True)
    user_id = fields.Many2one("res.users", required=True, index=True, ondelete="cascade")
    company_id = fields.Many2one("res.company", required=True, index=True, ondelete="cascade")
    prefix = fields.Char(readonly=True, index=True)
    secret_hash = fields.Char(readonly=True, index=True, groups="base.group_system")
    scope = fields.Selection([("read", "Read only"), ("quote", "Read and propose quotations")], required=True, default="read")
    model_permissions = fields.Json(default=dict, help="Explicit MCP tool permissions by supported Odoo model. Core access rights still apply.")
    active = fields.Boolean(default=True, index=True)
    expires_at = fields.Datetime(required=True, index=True)
    last_used_at = fields.Datetime(readonly=True)
    last_client = fields.Char(readonly=True)
    revoked_at = fields.Datetime(readonly=True)
    window_start = fields.Datetime(readonly=True)
    window_count = fields.Integer(readonly=True, default=0)

    _secret_hash_unique = models.Constraint("unique(secret_hash)", "Connection key must be unique.")

    @api.model
    def _hash(self, secret):
        return hashlib.sha256(str(secret or "").encode("utf-8")).hexdigest()

    @api.model
    def _permissions(self):
        self.ensure_one()
        if not isinstance(self.model_permissions, dict):
            # Existing 20.0.1.0.0 keys keep their original capabilities after upgrade.
            return self._normalize_permissions(None, self.scope)
        return self.model_permissions

    @api.model
    def _normalize_permissions(self, permissions, scope):
        allowed = {"res.partner": {"lookup"}, "product.product": {"lookup"},
                   "sale.order": {"briefing", "propose"}}
        if permissions is None:
            permissions = {"res.partner": ["lookup"], "product.product": ["lookup"],
                           "sale.order": ["briefing"] + (["propose"] if scope == "quote" else [])}
        if not isinstance(permissions, dict) or set(permissions) - set(allowed):
            raise ValidationError("Danh sách model MCP không hợp lệ.")
        normalized = {}
        for model_name, operations in permissions.items():
            if (not isinstance(operations, list) or any(not isinstance(op, str) for op in operations)
                    or len(operations) != len(set(operations)) or set(operations) - allowed[model_name]):
                raise ValidationError("Quyền MCP cho model không hợp lệ.")
            if "propose" in operations and scope != "quote":
                raise AccessError("Quyền đề xuất báo giá cần phạm vi báo giá.")
            if operations:
                normalized[model_name] = sorted(operations)
        return normalized

    def permits(self, model_name, operation):
        self.ensure_one()
        return operation in self._permissions().get(model_name, [])

    def require_permission(self, model_name, operation):
        if not self.permits(model_name, operation):
            raise AccessError("MODEL_PERMISSION_DENIED")

    @api.model
    def issue(self, name, user_id=None, company_id=None, scope="read", days=30, permissions=None):
        actor = self.env.user
        manager = actor.has_group("erpcloud_mcp_center.group_mcp_center_manager") or actor.has_group("base.group_system")
        target = self.env["res.users"].sudo().browse(int(user_id or actor.id)).exists()
        company = self.env["res.company"].sudo().browse(int(company_id or self.env.company.id)).exists()
        label = str(name or "").strip()
        try:
            days = int(days)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Thời hạn phải là số ngày hợp lệ.") from exc
        if not target or not target.active or not company or company not in target.company_ids:
            raise AccessError("Người dùng không thuộc công ty đã chọn.")
        if target != actor and not manager:
            raise AccessError("Chỉ quản trị viên được cấp quyền cho người khác.")
        if scope not in ("read", "quote") or (scope == "quote" and not manager):
            raise AccessError("Phạm vi truy cập không được phép.")
        if not label or len(label) > 120 or not 1 <= days <= 90:
            raise ValidationError("Tên kết nối hoặc thời hạn không hợp lệ.")
        permissions = self._normalize_permissions(permissions, scope)
        secret = secrets.token_urlsafe(48)
        record = self.sudo().create({
            "name": label, "user_id": target.id, "company_id": company.id,
            "scope": scope, "prefix": secret[:8], "secret_hash": self._hash(secret),
            "model_permissions": permissions,
            "expires_at": fields.Datetime.add(fields.Datetime.now(), days=days),
        })
        return record, secret

    @api.model
    def authenticate(self, secret):
        if not isinstance(secret, str) or len(secret) < 40:
            return self.browse()
        key = self.sudo().search([
            ("secret_hash", "=", self._hash(secret)), ("active", "=", True),
            ("expires_at", ">", fields.Datetime.now()), ("user_id.active", "=", True),
        ], limit=1)
        if key and key.company_id not in key.user_id.company_ids:
            return self.browse()
        return key

    def revoke_for_actor(self):
        actor = self.env.user
        manager = actor.has_group("erpcloud_mcp_center.group_mcp_center_manager") or actor.has_group("base.group_system")
        for key in self:
            if key.user_id != actor and not manager:
                raise AccessError("Bạn chỉ có thể ngắt kết nối của mình.")
        self.sudo().write({"active": False, "revoked_at": fields.Datetime.now()})
        return True

    def consume(self, client_name=""):
        """Per-key one-minute budget; lock prevents concurrent requests bypassing it."""
        self.ensure_one()
        self.env.cr.execute("SELECT id FROM erpcloud_mcp_center_key WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(["window_start", "window_count"])
        now = fields.Datetime.now()
        if not self.window_start or (now - self.window_start).total_seconds() >= 60:
            values = {"window_start": now, "window_count": 1}
        else:
            if self.window_count >= 60:
                raise AccessError("MCP_RATE_LIMIT")
            values = {"window_count": self.window_count + 1}
        values.update({"last_used_at": now, "last_client": str(client_name or "")[:80]})
        self.sudo().write(values)
