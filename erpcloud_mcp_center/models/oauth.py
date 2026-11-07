"""Hashed OAuth 2.1 credentials for standards-based MCP clients."""
import hashlib
import secrets

from odoo import api, fields, models


def oauth_hash(value):
    return hashlib.sha256(str(value or "").encode()).hexdigest()


class MCPOAuthClient(models.Model):
    _name = "erpcloud.mcp.center.oauth.client"
    _description = "ERPCloud MCP OAuth Client"

    name = fields.Char(required=True)
    client_id = fields.Char(required=True, index=True, default=lambda self: secrets.token_urlsafe(24))
    client_secret_hash = fields.Char(groups="base.group_system")
    redirect_uris = fields.Json(required=True, default=list)
    active = fields.Boolean(default=True)
    registration_ip = fields.Char(groups="base.group_system")
    _client_id_unique = models.Constraint(
        "unique(client_id)", "OAuth client ID must be unique."
    )


class MCPOAuthCode(models.Model):
    _name = "erpcloud.mcp.center.oauth.code"
    _description = "ERPCloud MCP OAuth Authorization Code"

    code_hash = fields.Char(required=True, index=True, groups="base.group_system")
    client_id = fields.Many2one("erpcloud.mcp.center.oauth.client", required=True, ondelete="cascade")
    key_id = fields.Many2one("erpcloud.mcp.center.key", required=True, ondelete="cascade")
    redirect_uri = fields.Char(required=True)
    code_challenge = fields.Char(required=True)
    scope = fields.Char(required=True, default="read")
    expires_at = fields.Datetime(required=True, index=True)
    consumed_at = fields.Datetime(index=True)


class MCPOAuthAccessToken(models.Model):
    _name = "erpcloud.mcp.center.oauth.access.token"
    _description = "ERPCloud MCP OAuth Access Token"

    token_hash = fields.Char(required=True, index=True, groups="base.group_system")
    family_id = fields.Char(required=True, index=True, groups="base.group_system")
    key_id = fields.Many2one("erpcloud.mcp.center.key", required=True, ondelete="cascade")
    client_id = fields.Many2one("erpcloud.mcp.center.oauth.client", required=True, ondelete="cascade")
    scope = fields.Char(required=True, default="read")
    expires_at = fields.Datetime(required=True, index=True)
    revoked_at = fields.Datetime(index=True)
    _access_hash_unique = models.Constraint(
        "unique(token_hash)", "OAuth token must be unique."
    )

    @api.model
    def resolve_active(self, raw):
        return self.sudo().search([
            ("token_hash", "=", oauth_hash(raw)), ("revoked_at", "=", False),
            ("expires_at", ">", fields.Datetime.now()), ("client_id.active", "=", True),
            ("key_id.active", "=", True), ("key_id.expires_at", ">", fields.Datetime.now()),
        ], limit=1)


class MCPOAuthRefreshToken(models.Model):
    _name = "erpcloud.mcp.center.oauth.refresh.token"
    _description = "ERPCloud MCP OAuth Refresh Token"

    token_hash = fields.Char(required=True, index=True, groups="base.group_system")
    family_id = fields.Char(required=True, index=True, groups="base.group_system")
    key_id = fields.Many2one("erpcloud.mcp.center.key", required=True, ondelete="cascade")
    client_id = fields.Many2one("erpcloud.mcp.center.oauth.client", required=True, ondelete="cascade")
    scope = fields.Char(required=True, default="read")
    expires_at = fields.Datetime(required=True, index=True)
    used_at = fields.Datetime(index=True)
    revoked_at = fields.Datetime(index=True)
    _refresh_hash_unique = models.Constraint(
        "unique(token_hash)", "OAuth refresh token must be unique."
    )

    def revoke_family(self):
        for row in self:
            now = fields.Datetime.now()
            self.sudo().search([("family_id", "=", row.family_id), ("revoked_at", "=", False)]).write({"revoked_at": now})
            self.env["erpcloud.mcp.center.oauth.access.token"].sudo().search([
                ("family_id", "=", row.family_id), ("revoked_at", "=", False),
            ]).write({"revoked_at": now})
