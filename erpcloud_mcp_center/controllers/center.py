"""Small UI API. Core business work is always run with the real Odoo user."""
import uuid
from urllib.parse import urlparse

from odoo import fields, http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request


def _manager():
    user = request.env.user
    return user.has_group("erpcloud_mcp_center.group_mcp_center_manager") or user.has_group("base.group_system")


def _approver():
    user = request.env.user
    return user.has_group("erpcloud_mcp_center.group_mcp_center_approver") or user.has_group("base.group_system")


def _key_payload(key):
    return {"id": key.id, "name": key.name, "prefix": key.prefix,
            "scope": key.scope, "permissions": key._permissions(), "active": key.active,
            "owner": key.user_id.name, "company": key.company_id.name,
            "expires_at": fields.Datetime.to_string(key.expires_at),
            "last_used_at": fields.Datetime.to_string(key.last_used_at) if key.last_used_at else ""}


def _proposal_payload(row):
    return {"id": row.id, "state": row.state, "requester": row.requester_id.name,
            "partner": row.partner_id.display_name, "preview": row.preview_json,
            "expires_at": fields.Datetime.to_string(row.expires_at),
            "sale_order_id": row.sale_order_id.id if row.sale_order_id else None,
            "decision_at": fields.Datetime.to_string(row.decision_at) if row.decision_at else ""}


class MCPCenterController(http.Controller):
    @http.route("/erpcloud_mcp_center/bootstrap", type="jsonrpc", auth="user")
    def bootstrap(self):
        env = request.env
        user, company = env.user, env.company
        keys = env["erpcloud.mcp.center.key"].sudo().search([
            ("company_id", "=", company.id),
            *(([] if _manager() else [("user_id", "=", user.id)])),
        ], order="create_date desc", limit=50)
        proposals = env["erpcloud.mcp.center.proposal"].sudo().search([
            ("company_id", "=", company.id),
            *(([] if _approver() else [("requester_id", "=", user.id)])),
        ], order="create_date desc", limit=30)
        audits = env["erpcloud.mcp.center.audit"].sudo().search([
            ("company_id", "=", company.id),
            *(([] if _manager() else [("user_id", "=", user.id)])),
        ], order="create_date desc", limit=15)
        base = env["ir.config_parameter"].sudo().get_str("web.base.url", request.httprequest.url_root.rstrip("/")).rstrip("/")
        host = urlparse(base).hostname or ""
        return {
            "user": {"id": user.id, "name": user.name},
            "company": {"id": company.id, "name": company.name},
            "is_manager": _manager(), "is_approver": _approver(),
            "url": base + "/mcp", "local_only": host in ("127.0.0.1", "localhost", "::1"),
            "keys": [_key_payload(key) for key in keys],
            "proposals": [_proposal_payload(row) for row in proposals],
            "activity": [{"trace_id": row.trace_id, "tool": row.tool, "status": row.status,
                          "code": row.code, "time": fields.Datetime.to_string(row.create_date)} for row in audits],
        }

    @http.route("/erpcloud_mcp_center/issue", type="jsonrpc", auth="user")
    def issue(self, name, scope="read", days=30, user_id=None, permissions=None):
        record, secret = request.env["erpcloud.mcp.center.key"].issue(
            name, user_id=user_id, scope=scope, days=days, permissions=permissions,
        )
        return {"key": _key_payload(record), "secret": secret}

    @http.route("/erpcloud_mcp_center/models_catalog", type="jsonrpc", auth="user")
    def models_catalog(self, query=""):
        return request.env["erpcloud.mcp.center.gateway"].catalog(query=query)

    @http.route("/erpcloud_mcp_center/revoke", type="jsonrpc", auth="user")
    def revoke(self, key_id):
        key = request.env["erpcloud.mcp.center.key"].sudo().browse(int(key_id)).exists()
        if not key or key.company_id != request.env.company:
            raise AccessError("Không tìm thấy kết nối trong công ty này.")
        key.with_user(request.env.user).revoke_for_actor()
        return {"ok": True}

    @http.route("/erpcloud_mcp_center/rotate", type="jsonrpc", auth="user")
    def rotate(self, key_id):
        key = request.env["erpcloud.mcp.center.key"].sudo().browse(int(key_id)).exists()
        if not key or key.company_id != request.env.company or not key.active:
            raise AccessError("Kết nối không còn hiệu lực.")
        if key.user_id != request.env.user and not _manager():
            raise AccessError("Bạn chỉ có thể đổi khóa của mình.")
        if key.scope in ("quote", "write") and not _manager():
            raise AccessError("Quản trị viên phải đổi khóa có quyền ghi dữ liệu.")
        created, secret = request.env["erpcloud.mcp.center.key"].issue(
            key.name + " (mới)", user_id=key.user_id.id,
            company_id=key.company_id.id, scope=key.scope, days=30,
            permissions=key._permissions(),
        )
        key.with_user(request.env.user).revoke_for_actor()
        return {"key": _key_payload(created), "secret": secret}

    @http.route("/erpcloud_mcp_center/search", type="jsonrpc", auth="user")
    def search(self, kind, query=""):
        env = request.env
        query = str(query or "").strip()[:80]
        if len(query) < 2:
            return []
        if kind == "partner":
            model = env["res.partner"].with_company(env.company).with_context(allowed_company_ids=[env.company.id])
            rows = model.search([("name", "ilike", query)], limit=12)
        elif kind == "product":
            model = env["product.product"].with_company(env.company).with_context(allowed_company_ids=[env.company.id])
            rows = model.search([("sale_ok", "=", True), ("active", "=", True),
                                 ("name", "ilike", query), ("company_id", "in", [False, env.company.id])], limit=12)
        else:
            raise ValidationError("Loại tìm kiếm không hợp lệ.")
        return [{"id": row.id, "name": row.display_name} for row in rows]

    @http.route("/erpcloud_mcp_center/propose", type="jsonrpc", auth="user")
    def propose(self, key_id, partner_id, lines, note=""):
        key = request.env["erpcloud.mcp.center.key"].sudo().browse(int(key_id)).exists()
        if not key or key.user_id != request.env.user or key.company_id != request.env.company or not key.active or key.expires_at <= fields.Datetime.now():
            raise AccessError("Kết nối tạo báo giá không hợp lệ.")
        proposal = request.env["erpcloud.mcp.center.proposal"].propose(
            key, {"partner_id": partner_id, "lines": lines, "note": note}, str(uuid.uuid4()),
        )
        return _proposal_payload(proposal)

    @http.route("/erpcloud_mcp_center/decide", type="jsonrpc", auth="user")
    def decide(self, proposal_id, approve, note=""):
        if not _approver():
            raise AccessError("Bạn cần quyền duyệt báo giá AI.")
        proposal = request.env["erpcloud.mcp.center.proposal"].sudo().browse(int(proposal_id)).exists()
        if not proposal or proposal.company_id != request.env.company:
            raise AccessError("Không tìm thấy đề xuất trong công ty này.")
        order = proposal.with_user(request.env.user).decide(bool(approve), note)
        return {"proposal": _proposal_payload(proposal),
                "order_url": "/web#id=%s&model=sale.order&view_type=form" % order.id if order else ""}
