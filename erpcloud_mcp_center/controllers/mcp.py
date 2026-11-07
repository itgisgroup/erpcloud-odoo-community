"""Small native Streamable HTTP MCP endpoint for curated business tools."""
import json
import secrets
import time
import uuid

from odoo import fields, http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request

from ..protocol.engine import MCPProtocolEngine, MCPProtocolError, MCPSession


def _reply(body=None, status=200, headers=None):
    common = [("Cache-Control", "no-store"), ("Pragma", "no-cache")]
    common.extend(headers or [])
    if body is None:
        return request.make_response(b"", status=status, headers=common)
    return request.make_json_response(body, status=status, headers=common)


def _challenge(code="invalid_token", status=401):
    base = request.httprequest.url_root.rstrip("/")
    return _reply({"error": code}, status, [("WWW-Authenticate", 'Bearer resource_metadata="%s/.well-known/oauth-protected-resource"' % base)])


def _business_env(key, model):
    return request.env[model].with_user(key.user_id).with_company(key.company_id).with_context(allowed_company_ids=[key.company_id.id])


def _briefing(key, arguments):
    key.require_permission("sale.order", "briefing")
    if not isinstance(arguments, dict) or set(arguments) - {"days"}:
        raise ValidationError("Chỉ dùng tham số days.")
    try:
        days = int(arguments.get("days", 30))
    except (TypeError, ValueError) as exc:
        raise ValidationError("days phải là số ngày.") from exc
    if not 1 <= days <= 90:
        raise ValidationError("days phải từ 1 đến 90.")
    model = _business_env(key, "sale.order")
    model.check_access("read")
    since = fields.Datetime.subtract(fields.Datetime.now(), days=days)
    domain = [("company_id", "=", key.company_id.id), ("state", "in", ["draft", "sent"]), ("date_order", ">=", since)]
    if not key.user_id.has_group("sales_team.group_sale_manager"):
        domain.append(("user_id", "=", key.user_id.id))
    total = model.search_count(domain)
    orders = model.search(domain, order="date_order desc,id desc", limit=30)
    sums = {}
    items = []
    for order in orders:
        currency = order.currency_id.name
        sums[currency] = round(sums.get(currency, 0.0) + order.amount_total, 2)
        items.append({
            "id": order.id, "number": order.name, "customer": order.partner_id.display_name,
            "amount": order.amount_total, "currency": currency,
            "date": fields.Datetime.to_string(order.date_order), "state": order.state,
            "url": "/web#id=%s&model=sale.order&view_type=form" % order.id,
        })
    return {"company": key.company_id.name, "company_id": key.company_id.id,
            "period_days": days, "as_of": fields.Datetime.to_string(fields.Datetime.now()),
            "total_count": total, "sample_count": len(items), "sample_by_currency": sums,
            "orders": items, "more_available": total > len(items)}


def _lookup(key, arguments, model_name):
    key.require_permission(model_name, "lookup")
    if not isinstance(arguments, dict) or set(arguments) != {"query"}:
        raise ValidationError("Provide a single query value.")
    query = str(arguments["query"] or "").strip()[:80]
    if len(query) < 2:
        raise ValidationError("Search for at least two characters.")
    model = _business_env(key, model_name)
    model.check_access("read")
    if model_name == "res.partner":
        domain = [("company_id", "in", [False, key.company_id.id]),
                  "|", ("name", "ilike", query), ("email", "ilike", query)]
    else:
        domain = [("company_id", "in", [False, key.company_id.id]),
                  ("active", "=", True), ("sale_ok", "=", True),
                  "|", ("name", "ilike", query), ("default_code", "ilike", query)]
    rows = model.search(domain, limit=10, order="name,id")
    return {"query": query, "company": key.company_id.name,
            "matches": [{"id": row.id, "name": row.display_name,
                         "url": "/web#id=%s&model=%s&view_type=form" % (row.id, model_name)} for row in rows]}


def _tools(key, oauth_write):
    tools = [
        {"name": "whoami", "description": "Show the current Odoo user, company and allowed connection scope.",
         "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
         "annotations": {"readOnlyHint": True, "destructiveHint": False}},
        {"name": "sales_followup_briefing", "description": "Summarize recent draft and sent quotations with source record links. Respects Odoo access rights.",
         "inputSchema": {"type": "object", "properties": {"days": {"type": "integer", "minimum": 1, "maximum": 90}}, "additionalProperties": False},
         "annotations": {"readOnlyHint": True, "destructiveHint": False}},
        {"name": "customer_lookup", "description": "Find a customer by name or email within your Odoo company and read rights. Use the returned ID for quotation proposals.",
         "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "minLength": 2, "maxLength": 80}}, "required": ["query"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True, "destructiveHint": False}},
        {"name": "product_lookup", "description": "Find a saleable product by name or SKU within your Odoo company and read rights. Use the returned ID for quotation proposals.",
         "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "minLength": 2, "maxLength": 80}}, "required": ["query"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True, "destructiveHint": False}},
    ]
    tools = [tool for tool in tools if tool["name"] == "whoami" or {
        "sales_followup_briefing": key.permits("sale.order", "briefing"),
        "customer_lookup": key.permits("res.partner", "lookup"),
        "product_lookup": key.permits("product.product", "lookup"),
    }.get(tool["name"], False)]
    grants = key._permissions()
    if any("read" in ops for ops in grants.values()):
        tools.extend([
            {"name": "list_models", "description": "List Odoo models explicitly granted to this connection and their allowed operations.",
             "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
             "annotations": {"readOnlyHint": True, "destructiveHint": False}},
            {"name": "get_fields", "description": "List readable fields for one granted Odoo model. Sensitive and binary fields are excluded.",
             "inputSchema": {"type": "object", "properties": {"model": {"type": "string"}}, "required": ["model"], "additionalProperties": False},
             "annotations": {"readOnlyHint": True, "destructiveHint": False}},
            {"name": "search_records", "description": "Search granted Odoo model records by display name. Returns source links and limited selected fields.",
             "inputSchema": {"type": "object", "properties": {"model": {"type": "string"}, "query": {"type": "string"},
                 "fields": {"type": "array", "items": {"type": "string"}, "maxItems": 20}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}},
                 "required": ["model"], "additionalProperties": False},
             "annotations": {"readOnlyHint": True, "destructiveHint": False}},
            {"name": "get_record", "description": "Read one record of a granted Odoo model and return its source link.",
             "inputSchema": {"type": "object", "properties": {"model": {"type": "string"}, "id": {"type": "integer", "minimum": 1},
                 "fields": {"type": "array", "items": {"type": "string"}, "maxItems": 20}},
                 "required": ["model", "id"], "additionalProperties": False},
             "annotations": {"readOnlyHint": True, "destructiveHint": False}},
        ])
    if oauth_write:
        schema = {"model": {"type": "string"}, "request_key": {"type": "string", "minLength": 8, "maxLength": 128}}
        if any("create" in ops for ops in grants.values()):
            tools.append({"name": "create_record", "description": "Create one record in a specifically granted model. Use a stable request_key so retries do not duplicate it.",
                          "inputSchema": {"type": "object", "properties": {**schema, "values": {"type": "object"}},
                                          "required": ["model", "values", "request_key"], "additionalProperties": False},
                          "annotations": {"readOnlyHint": False, "destructiveHint": False}})
        if any("write" in ops for ops in grants.values()):
            tools.append({"name": "update_record", "description": "Update one record in a specifically granted model. Use a stable request_key for safe retry.",
                          "inputSchema": {"type": "object", "properties": {**schema, "id": {"type": "integer", "minimum": 1}, "values": {"type": "object"}},
                                          "required": ["model", "id", "values", "request_key"], "additionalProperties": False},
                          "annotations": {"readOnlyHint": False, "destructiveHint": False}})
        if any("unlink" in ops for ops in grants.values()):
            tools.append({"name": "delete_record", "description": "Permanently delete one record in a specifically granted model. Requires exact confirmation DELETE <model> <id> and a stable request_key.",
                          "inputSchema": {"type": "object", "properties": {**schema, "id": {"type": "integer", "minimum": 1}, "confirm": {"type": "string"}},
                                          "required": ["model", "id", "confirm", "request_key"], "additionalProperties": False},
                          "annotations": {"readOnlyHint": False, "destructiveHint": True}})
    if key.scope == "quote" and oauth_write and key.permits("sale.order", "propose"):
        tools.append({
            "name": "quotation_propose",
            "description": "Prepare an exact quotation preview for human review. This does not create or confirm a sale order. An authorized approver must approve in MCP Center.",
            "inputSchema": {"type": "object", "properties": {
                "partner_id": {"type": "integer", "minimum": 1},
                "lines": {"type": "array", "minItems": 1, "maxItems": 20,
                          "items": {"type": "object", "properties": {
                              "product_id": {"type": "integer", "minimum": 1},
                              "quantity": {"type": "number", "exclusiveMinimum": 0}},
                              "required": ["product_id", "quantity"], "additionalProperties": False}},
                "note": {"type": "string", "maxLength": 500},
                "request_key": {"type": "string", "minLength": 8, "maxLength": 128},
            }, "required": ["partner_id", "lines", "request_key"], "additionalProperties": False},
            "annotations": {"readOnlyHint": False, "destructiveHint": False},
        })
    return tools


class MCPController(http.Controller):
    @http.route("/mcp", type="http", auth="none", methods=["POST", "GET", "DELETE"], csrf=False)
    def mcp(self, **kwargs):
        method = request.httprequest.method
        if method == "GET":
            return _reply({"error": "sse_get_not_supported"}, 405, [("Allow", "POST, DELETE")])
        origin = request.httprequest.headers.get("Origin")
        if origin:
            own = request.httprequest.url_root.rstrip("/")
            allowed = {own} | {x.strip() for x in (request.env["ir.config_parameter"].sudo().get_str("erpcloud_mcp_center.allowed_origins") or "").split(",") if x.strip()}
            if origin not in allowed:
                return _reply({"error": "origin_not_allowed"}, 403)
        auth = request.httprequest.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return _challenge("missing_bearer_token")
        bearer = auth[7:].strip()
        key = request.env["erpcloud.mcp.center.key"].sudo().authenticate(bearer)
        oauth_access = request.env["erpcloud.mcp.center.oauth.access.token"].sudo().resolve_active(bearer) if not key else False
        if oauth_access:
            key = oauth_access.key_id
        if not key:
            return _challenge()
        oauth_write = not oauth_access or "write" in set((oauth_access.scope or "").split())
        try:
            key.consume(request.httprequest.headers.get("User-Agent", ""))
        except AccessError:
            return _reply({"error": "rate_limited"}, 429, [("Retry-After", "60")])
        Session = request.env["erpcloud.mcp.center.session"].sudo()
        sid = request.httprequest.headers.get("Mcp-Session-Id", "")
        if method == "DELETE":
            row = Session.search([("session_id", "=", sid), ("key_id", "=", key.id)], limit=1)
            if not row:
                return _reply({"error": "session_not_found"}, 404)
            row.unlink()
            return _reply(None, 204)
        if request.httprequest.content_type.split(";", 1)[0] != "application/json":
            return _reply({"error": "content_type_must_be_application_json"}, 415)
        raw = request.httprequest.get_data()
        if len(raw) > 1024 * 1024:
            return _reply({"error": "request_too_large"}, 413)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return _reply({"error": "invalid_json"}, 400)
        if not isinstance(payload, dict):
            return _reply({"error": "invalid_request"}, 400)
        row = Session.search([("session_id", "=", sid), ("key_id", "=", key.id)], limit=1) if sid else Session
        if sid and not row:
            return _reply({"error": "session_not_found"}, 404)
        if not sid and payload.get("method") != "initialize":
            return _reply({"error": "initialize_required"}, 400)
        if not sid:
            sid = secrets.token_urlsafe(24)
            row = Session.create({"session_id": sid, "key_id": key.id, "company_id": key.company_id.id})
        if (request.httprequest.headers.get("MCP-Protocol-Version") and row.protocol_version
                and request.httprequest.headers["MCP-Protocol-Version"] != row.protocol_version):
            return _reply({"error": "protocol_version_mismatch"}, 400)
        session = MCPSession(sid, key.user_id.id, row.client_name, row.client_version, row.protocol_version, row.initialized)
        def tool_call(_session, name, arguments):
            trace = str(uuid.uuid4())
            started = time.monotonic()
            status, code, target_model, target_id = "ok", "", "", 0
            try:
                if name == "whoami":
                    if arguments:
                        raise ValidationError("whoami không nhận tham số.")
                    result = {"user": key.user_id.name, "company": key.company_id.name,
                              "company_id": key.company_id.id, "scope": key.scope,
                              "model_permissions": key._permissions()}
                elif name == "sales_followup_briefing":
                    result = _briefing(key, arguments)
                elif name == "customer_lookup":
                    result = _lookup(key, arguments, "res.partner")
                elif name == "product_lookup":
                    result = _lookup(key, arguments, "product.product")
                elif name in {"list_models", "get_fields", "search_records", "get_record", "create_record", "update_record", "delete_record"}:
                    if not isinstance(arguments, dict):
                        raise ValidationError("Tool arguments must be an object.")
                    allowed_arguments = {
                        "list_models": set(), "get_fields": {"model"},
                        "search_records": {"model", "query", "fields", "limit"},
                        "get_record": {"model", "id", "fields"},
                        "create_record": {"model", "values", "request_key"},
                        "update_record": {"model", "id", "values", "request_key"},
                        "delete_record": {"model", "id", "confirm", "request_key"},
                    }
                    if set(arguments) - allowed_arguments[name] or name not in {tool["name"] for tool in _tools(key, oauth_write)}:
                        raise AccessError("Tool or arguments not allowed for this connection.")
                    gateway = request.env["erpcloud.mcp.center.gateway"]
                    model_name = arguments.get("model")
                    if name == "list_models":
                        result = {"models": [{"model": model, "operations": ops} for model, ops in key._permissions().items() if "read" in ops]}
                    elif name == "get_fields":
                        result = gateway.list_fields(key, model_name)
                    elif name == "search_records":
                        result = gateway.search_records(key, model_name, arguments.get("query", ""), arguments.get("fields"), arguments.get("limit", 10))
                    elif name == "get_record":
                        result = gateway.get_record(key, model_name, arguments.get("id"), arguments.get("fields"))
                    else:
                        if not oauth_write:
                            raise AccessError("OAuth write consent is required.")
                        target_model = model_name
                        if name == "create_record":
                            result = gateway.create_record(key, model_name, arguments.get("values"), arguments.get("request_key"))
                        elif name == "update_record":
                            result = gateway.update_record(key, model_name, arguments.get("id"), arguments.get("values"), arguments.get("request_key"))
                        else:
                            result = gateway.delete_record(key, model_name, arguments.get("id"), arguments.get("confirm"), arguments.get("request_key"))
                        target_id = result.get("id", 0)
                elif name == "quotation_propose" and key.scope == "quote" and oauth_write and key.permits("sale.order", "propose"):
                    if not isinstance(arguments, dict) or set(arguments) - {"partner_id", "lines", "note", "request_key"}:
                        raise ValidationError("Tham số báo giá không hợp lệ.")
                    inputs = {k: arguments[k] for k in ("partner_id", "lines", "note") if k in arguments}
                    proposal = request.env["erpcloud.mcp.center.proposal"].with_user(key.user_id).with_company(key.company_id).propose(key, inputs, arguments.get("request_key"))
                    target_model, target_id = "erpcloud.mcp.center.proposal", proposal.id
                    result = {"proposal_id": proposal.id, "state": proposal.state,
                              "expires_at": fields.Datetime.to_string(proposal.expires_at),
                              "preview": proposal.preview_json,
                              "next_action": "Open MCP Center > Cần duyệt to review and approve."}
                else:
                    status, code = "denied", "TOOL_NOT_ALLOWED"
                    raise MCPProtocolError(-32003, "Tool not allowed for this connection", {"code": code})
                result["trace_id"] = trace
                return result
            except (AccessError, ValidationError, MCPProtocolError) as exc:
                status, code = "denied", type(exc).__name__
                if isinstance(exc, MCPProtocolError):
                    raise
                raise MCPProtocolError(-32003 if isinstance(exc, AccessError) else -32602,
                                       "Access denied" if isinstance(exc, AccessError) else str(exc),
                                       {"code": code, "trace_id": trace}) from exc
            except Exception as exc:
                status, code = "error", type(exc).__name__
                raise MCPProtocolError(-32603, "Business tool failed", {"code": "BUSINESS_TOOL_FAILED", "trace_id": trace}) from exc
            finally:
                request.env["erpcloud.mcp.center.audit"].sudo().create({
                    "trace_id": trace, "key_id": key.id, "user_id": key.user_id.id,
                    "company_id": key.company_id.id, "tool": name, "status": status,
                    "code": code, "duration_ms": int((time.monotonic() - started) * 1000),
                    "target_model": target_model, "target_id": target_id,
                })
        engine = MCPProtocolEngine(lambda _session, _params: {"tools": _tools(key, oauth_write)}, tool_call)
        try:
            result = engine.dispatch(session, payload)
        except MCPProtocolError as exc:
            result = {"jsonrpc": "2.0", "id": payload.get("id"),
                      "error": {"code": exc.code, "message": exc.message, "data": exc.data or {}}}
        row.write({"protocol_version": session.protocol_version, "client_name": session.client_name,
                   "client_version": session.client_version, "initialized": session.initialized,
                   "last_seen_at": fields.Datetime.now()})
        headers = [("Mcp-Session-Id", sid)]
        if result is None:
            return _reply(None, 202, headers)
        return _reply(result, 200, headers)
