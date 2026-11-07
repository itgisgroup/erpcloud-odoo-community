"""OAuth 2.1 + PKCE endpoints for standards-based MCP clients."""
import base64
import hashlib
import json
import re
import secrets
from html import escape
from urllib.parse import urlencode, urlparse

from odoo import fields, http
from odoo.http import request

from ..models.oauth import oauth_hash


_PKCE = re.compile(r"^[A-Za-z0-9_-]{43,128}$")


def _json(payload, status=200):
    return request.make_response(
        json.dumps(payload), status=status,
        headers=[("Content-Type", "application/json; charset=utf-8"),
                 ("Cache-Control", "no-store"), ("Pragma", "no-cache")],
    )


def _base():
    return request.httprequest.url_root.rstrip("/")


def _valid_redirect(uri):
    try:
        parsed = urlparse(str(uri))
    except ValueError:
        return False
    custom_scheme = bool(
        ("." in parsed.scheme or parsed.scheme in {"vscode", "cursor", "codex"})
        and re.fullmatch(r"[a-z][a-z0-9+.-]{1,80}", parsed.scheme)
        and parsed.path and not parsed.netloc
    )
    return bool(
        (parsed.scheme == "https" and parsed.netloc)
        or (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost", "::1"))
        or custom_scheme
    ) and not parsed.fragment and not parsed.username and not parsed.password


def _issue_tokens(key, client, scope, resource_uri, family=None):
    now = fields.Datetime.now()
    access, refresh = secrets.token_urlsafe(48), secrets.token_urlsafe(64)
    family = family or secrets.token_urlsafe(24)
    request.env["erpcloud.mcp.center.oauth.access.token"].sudo().create({
        "token_hash": oauth_hash(access), "family_id": family, "key_id": key.id,
        "client_id": client.id, "scope": scope, "resource_uri": resource_uri,
        "expires_at": fields.Datetime.add(now, minutes=15),
    })
    request.env["erpcloud.mcp.center.oauth.refresh.token"].sudo().create({
        "token_hash": oauth_hash(refresh), "family_id": family, "key_id": key.id,
        "client_id": client.id, "scope": scope, "resource_uri": resource_uri,
        "expires_at": fields.Datetime.add(now, days=30),
    })
    return {"token_type": "Bearer", "access_token": access, "expires_in": 900,
            "refresh_token": refresh, "scope": scope}


def _consent_html(client_name, redirect_uri, user_name, company_name, scopes, hidden, csrf_token, keys):
    options = "<option value='0'>Create a new read-only connection (recommended)</option>" + "".join(
        "<option value='%s'>%s — %s</option>" % (
            key.id, escape(key.name), escape(", ".join(
                "%s: %s" % (model, "/".join(operations))
                for model, operations in key._permissions().items())[:220])) for key in keys)
    write_keys = [key for key in keys if key.scope in ("write", "quote")]
    can_write = "write" in scopes and bool(write_keys)
    write_note = ("This application did not request write access." if "write" not in scopes
                  else "A manager must first create a write-enabled connection in MCP Center.")
    change_option = ("<label class='change'><input type='checkbox' name='allow_changes' value='1' %s>"
                     "<span><strong>Allow changes</strong><small>Only with an existing connection that permits them. "
                     "Without this, the assistant can only read.</small></span></label>" % ("" if can_write else "disabled"))
    if not can_write:
        change_option += "<small>%s</small>" % escape(write_note)
    return ("<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>ERPCloud MCP | Authorize</title><style>"
            "*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:#f3f8f6;color:#17332f;font:15px system-ui,sans-serif}"
            "main{width:min(530px,100%%);background:white;border:1px solid #e0eae5;border-radius:20px;padding:32px;box-shadow:0 24px 55px #113b2d15}"
            "header{display:flex;align-items:center;gap:10px;color:#0b735e;font-weight:800;letter-spacing:.3px}header b{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:#0b735e;color:white}"
            "h1{font-size:25px;letter-spacing:-.7px;margin:28px 0 6px}p{color:#637a72;line-height:1.6}.scope{padding:16px;margin:20px 0;border-radius:11px;background:#eff7f2;font-size:13px}"
            ".facts{display:grid;gap:9px;margin:18px 0}.facts div{display:grid;grid-template-columns:100px 1fr;gap:8px;font-size:13px}.facts span{color:#71847c}.facts strong{overflow-wrap:anywhere}"
            ".change{display:flex;gap:12px;align-items:flex-start;padding:14px;margin:16px 0;border:1px solid #d9e7e0;border-radius:10px}.change input{margin-top:3px;accent-color:#0a7159}.change strong,.change small{display:block}.change small{margin:5px 0 0}"
            "details{margin:14px 0 22px;color:#31594d;font-size:13px}summary{cursor:pointer;font-weight:700}select{display:block;width:100%%;padding:10px;margin:10px 0;border:1px solid #d9e7e0;border-radius:8px}"
            "button{width:100%%;border:0;border-radius:9px;background:#0a7159;color:white;padding:13px;font:700 14px system-ui;cursor:pointer}small{display:block;margin-top:16px;color:#8a9991;line-height:1.5}"
            "</style><main><header><b>✦</b> ERPCloud MCP Center</header><h1>Sign in as the user</h1>"
            "<p><strong>%s</strong> is requesting access to Odoo.</p>"
            "<div class='facts'><div><span>Signed in as</span><strong>%s</strong></div><div><span>Company</span><strong>%s</strong></div><div><span>Returns to</span><strong>%s</strong></div></div>"
            "<div class='scope'>Read access to customers, products and sales follow-up. Requested OAuth scope: <strong>%s</strong>.</div>"
            "<form method='post'>%s%s<details><summary>Choose an existing connection (optional)</summary>"
            "<select id='key_id' name='key_id'>%s</select><small>To allow changes, select a connection whose model rights were approved by an MCP Center manager.</small></details>"
            "<script>const k=document.getElementById('key_id'),w=document.querySelector('[name=allow_changes]');if(w&&!w.disabled){w.addEventListener('change',()=>{if(w.checked&&k.value==='0'){w.checked=false;k.closest('details').open=true;k.focus()}})}</script>"
            "<input type='hidden' name='csrf_token' value='%s'><button type='submit'>Sign in and allow</button></form>"
            "<small>Odoo rights and company rules still apply. Revoke this connection in MCP Center at any time.</small>"
            "</main></html>" % (escape(client_name), escape(user_name), escape(company_name),
                              escape(redirect_uri), escape(" ".join(sorted(scopes))), hidden,
                              change_option, options, escape(csrf_token)))


class MCPOAuthController(http.Controller):
    @http.route(["/.well-known/oauth-authorization-server", "/.well-known/oauth-authorization-server/mcp"], type="http", auth="none", methods=["GET"], csrf=False)
    def authorization_metadata(self, **kwargs):
        base = _base()
        return _json({
            "issuer": base, "authorization_endpoint": base + "/mcp/oauth/authorize",
            "token_endpoint": base + "/mcp/oauth/token",
            "registration_endpoint": base + "/mcp/oauth/register",
            "revocation_endpoint": base + "/mcp/oauth/revoke",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none"],
            "scopes_supported": ["read", "write", "offline_access"],
        })

    @http.route(["/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"], type="http", auth="none", methods=["GET"], csrf=False)
    def protected_resource_metadata(self, **kwargs):
        base = _base()
        return _json({"resource": base + "/mcp", "authorization_servers": [base],
                      "scopes_supported": ["read", "write", "offline_access"],
                      "bearer_methods_supported": ["header"]})

    @http.route("/mcp/oauth/register", type="http", auth="none", methods=["POST"], csrf=False)
    def register(self, **kwargs):
        try:
            value = json.loads(request.httprequest.get_data(as_text=True) or "{}")
        except ValueError:
            return _json({"error": "invalid_client_metadata"}, 400)
        redirects = value.get("redirect_uris")
        if not isinstance(redirects, list) or not 1 <= len(redirects) <= 10 or any(not _valid_redirect(uri) for uri in redirects):
            return _json({"error": "invalid_redirect_uri"}, 400)
        registration_ip = request.httprequest.remote_addr or "unknown"
        recent = request.env["erpcloud.mcp.center.oauth.client"].sudo().search_count([
            ("registration_ip", "=", registration_ip),
            ("create_date", ">", fields.Datetime.subtract(fields.Datetime.now(), hours=1)),
        ])
        if recent >= 30:
            return _json({"error": "temporarily_unavailable",
                          "error_description": "registration_rate_limited"}, 429)
        client = request.env["erpcloud.mcp.center.oauth.client"].sudo().create({
            "name": str(value.get("client_name") or "MCP client")[:120],
            "redirect_uris": list(dict.fromkeys(redirects)),
            "registration_ip": registration_ip,
        })
        return _json({"client_id": client.client_id, "client_name": client.name,
                      "redirect_uris": client.redirect_uris,
                      "token_endpoint_auth_method": "none"}, 201)

    @http.route("/mcp/oauth/authorize", type="http", auth="user", methods=["GET", "POST"], csrf=True)
    def authorize(self, **kwargs):
        p = request.params
        client = request.env["erpcloud.mcp.center.oauth.client"].sudo().search([
            ("client_id", "=", p.get("client_id")), ("active", "=", True),
        ], limit=1)
        redirect_uri = str(p.get("redirect_uri") or "")
        challenge = str(p.get("code_challenge") or "")
        scopes = set(str(p.get("scope") or "read").split())
        if (not client or redirect_uri not in (client.redirect_uris or [])
                or p.get("response_type") != "code" or p.get("code_challenge_method") != "S256"
                or not _PKCE.fullmatch(challenge) or not scopes or not scopes <= {"read", "write", "offline_access"}
                or (p.get("resource") and p.get("resource").rstrip("/") != _base() + "/mcp")):
            return request.make_response("Invalid OAuth authorization request.", status=400)
        key_domain = [
            ("user_id", "=", request.env.user.id), ("company_id", "=", request.env.company.id),
            ("active", "=", True), ("expires_at", ">", fields.Datetime.now()),
        ]
        keys = request.env["erpcloud.mcp.center.key"].sudo().search(key_domain, order="id desc", limit=30)
        if request.httprequest.method == "GET":
            hidden = "".join('<input type="hidden" name="%s" value="%s">' % (escape(name), escape(str(p.get(name) or ""))) for name in ("client_id", "redirect_uri", "response_type", "code_challenge", "code_challenge_method", "scope", "state", "resource"))
            html = _consent_html(client.name, redirect_uri, request.env.user.name,
                                 request.env.company.name, scopes, hidden, request.csrf_token(), keys)
            return request.make_response(html, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])
        try:
            selected_key_id = int(p.get("key_id") or 0)
        except (TypeError, ValueError):
            selected_key_id = 0
        allow_changes = p.get("allow_changes") == "1"
        key = keys.filtered(lambda row: row.id == selected_key_id)[:1] if selected_key_id else False
        if selected_key_id and not key:
            return request.make_response("Select an authorized MCP connection.", status=403)
        if allow_changes and ("write" not in scopes or not key or key.scope not in ("write", "quote")):
            return request.make_response("A preapproved write connection is required for changes.", status=403)
        if not key:
            key, _secret = request.env["erpcloud.mcp.center.key"].issue(
                "OAuth: %s" % client.name, scope="read", days=30)
        granted_scopes = {"read"} | ({"offline_access"} if "offline_access" in scopes else set())
        if allow_changes:
            granted_scopes.add("write")
        raw_code = secrets.token_urlsafe(48)
        request.env["erpcloud.mcp.center.oauth.code"].sudo().create({
            "code_hash": oauth_hash(raw_code), "client_id": client.id, "key_id": key.id,
            "redirect_uri": redirect_uri, "code_challenge": challenge,
            "scope": " ".join(sorted(granted_scopes)), "resource_uri": _base() + "/mcp",
            "expires_at": fields.Datetime.add(fields.Datetime.now(), minutes=5),
        })
        query = {"code": raw_code}
        if p.get("state"):
            query["state"] = p["state"]
        separator = "&" if "?" in redirect_uri else "?"
        return request.redirect(redirect_uri + separator + urlencode(query), local=False)

    @http.route("/mcp/oauth/token", type="http", auth="none", methods=["POST"], csrf=False)
    def token(self, **kwargs):
        p = request.params
        client = request.env["erpcloud.mcp.center.oauth.client"].sudo().search([
            ("client_id", "=", p.get("client_id")), ("active", "=", True),
        ], limit=1)
        if not client:
            return _json({"error": "invalid_client"}, 401)
        if p.get("grant_type") == "authorization_code":
            verifier = str(p.get("code_verifier") or "")
            challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
            code = request.env["erpcloud.mcp.center.oauth.code"].sudo().search([
                ("code_hash", "=", oauth_hash(p.get("code"))), ("client_id", "=", client.id),
                ("redirect_uri", "=", p.get("redirect_uri")), ("consumed_at", "=", False),
                ("expires_at", ">", fields.Datetime.now()),
            ], limit=1)
            if not code or not secrets.compare_digest(code.code_challenge, challenge):
                return _json({"error": "invalid_grant"}, 400)
            if p.get("resource") and p.get("resource").rstrip("/") != code.resource_uri:
                return _json({"error": "invalid_target"}, 400)
            code.consumed_at = fields.Datetime.now()
            return _json(_issue_tokens(code.key_id, client, code.scope, code.resource_uri))
        if p.get("grant_type") == "refresh_token":
            token = request.env["erpcloud.mcp.center.oauth.refresh.token"].sudo().search([
                ("token_hash", "=", oauth_hash(p.get("refresh_token"))),
                ("client_id", "=", client.id), ("revoked_at", "=", False),
                ("expires_at", ">", fields.Datetime.now()),
            ], limit=1)
            if not token or token.used_at:
                if token:
                    token.revoke_family()
                return _json({"error": "invalid_grant"}, 400)
            if p.get("resource") and p.get("resource").rstrip("/") != token.resource_uri:
                return _json({"error": "invalid_target"}, 400)
            token.used_at = fields.Datetime.now()
            return _json(_issue_tokens(token.key_id, client, token.scope,
                                       token.resource_uri, token.family_id))
        return _json({"error": "unsupported_grant_type"}, 400)

    @http.route("/mcp/oauth/revoke", type="http", auth="none", methods=["POST"], csrf=False)
    def revoke(self, **kwargs):
        raw = request.params.get("token") or ""
        refresh = request.env["erpcloud.mcp.center.oauth.refresh.token"].sudo().search([
            ("token_hash", "=", oauth_hash(raw)),
        ], limit=1)
        if refresh:
            refresh.revoke_family()
        access = request.env["erpcloud.mcp.center.oauth.access.token"].sudo().search([
            ("token_hash", "=", oauth_hash(raw)),
        ], limit=1)
        if access:
            access.revoked_at = fields.Datetime.now()
        return _json({})
