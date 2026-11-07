from odoo import fields, models


class MCPAudit(models.Model):
    _name = "erpcloud.mcp.center.audit"
    _description = "MCP Center Activity"
    _order = "create_date desc, id desc"

    trace_id = fields.Char(required=True, index=True)
    key_id = fields.Many2one("erpcloud.mcp.center.key", ondelete="set null")
    user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    company_id = fields.Many2one("res.company", index=True, ondelete="set null")
    tool = fields.Char(index=True)
    status = fields.Selection([("ok", "Success"), ("denied", "Denied"), ("error", "Error")], required=True)
    code = fields.Char()
    duration_ms = fields.Integer()
    target_model = fields.Char()
    target_id = fields.Integer()
