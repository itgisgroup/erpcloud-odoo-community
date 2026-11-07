from odoo import fields, models


class MCPSession(models.Model):
    _name = "erpcloud.mcp.center.session"
    _description = "MCP Center Protocol Session"
    _order = "last_seen_at desc"

    session_id = fields.Char(required=True, index=True)
    key_id = fields.Many2one("erpcloud.mcp.center.key", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one("res.company", required=True, index=True)
    client_name = fields.Char()
    client_version = fields.Char()
    protocol_version = fields.Char()
    initialized = fields.Boolean(default=False)
    last_seen_at = fields.Datetime(default=fields.Datetime.now)

    _session_unique = models.Constraint("unique(session_id)", "MCP session ID must be unique.")
