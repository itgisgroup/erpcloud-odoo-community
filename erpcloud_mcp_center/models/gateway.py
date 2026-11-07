"""Original, model-agnostic MCP CRUD service governed by each connection key."""
import hashlib
import json
import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


_MODEL = re.compile(r"^[a-z][a-z0-9_.]{0,119}$")
_SENSITIVE = re.compile(r"(?:password|passwd|secret|token|api_key|private_key|credential)", re.I)
_READ_TYPES = {"char", "text", "boolean", "integer", "float", "monetary", "selection",
               "date", "datetime", "many2one"}
_WRITE_TYPES = _READ_TYPES - {"monetary"}


class MCPCrudRequest(models.Model):
    _name = "erpcloud.mcp.center.crud.request"
    _description = "MCP Center idempotent CRUD request"

    key_id = fields.Many2one("erpcloud.mcp.center.key", required=True, ondelete="cascade", index=True)
    request_key = fields.Char(required=True)
    payload_hash = fields.Char(required=True)
    result_json = fields.Json(required=True)

    _unique_request = models.Constraint("unique(key_id, request_key)", "Request key already used for this connection.")


class MCPGateway(models.AbstractModel):
    _name = "erpcloud.mcp.center.gateway"
    _description = "MCP Center dynamic model gateway"

    @api.model
    def catalog(self, key=None, query="", limit=30):
        query = str(query or "").strip()[:80]
        limit = max(1, min(int(limit), 50))
        domain = [("state", "=", "base")]
        if query:
            domain += ["|", ("name", "ilike", query), ("model", "ilike", query)]
        rows = self.env["ir.model"].sudo().search(domain, order="name,model", limit=250)
        result = []
        for row in rows:
            if not self.env["erpcloud.mcp.center.key"]._selectable_model(row.model):
                continue
            if key:
                available = set(key._permissions().get(row.model, []))
            else:
                model = self.env[row.model]
                available = set()
                for operation in ("read", "create", "write", "unlink"):
                    try:
                        model.check_access(operation)
                        available.add(operation)
                    except AccessError:
                        pass
            result.append({"model": row.model, "name": row.name, "operations": sorted(available)})
            if len(result) >= limit:
                break
        return result

    @api.model
    def _model(self, key, model_name, operation):
        if not isinstance(model_name, str) or not _MODEL.fullmatch(model_name):
            raise ValidationError("Invalid model name.")
        if not self.env["erpcloud.mcp.center.key"]._selectable_model(model_name):
            raise AccessError("Model is not available through MCP Center.")
        key.require_permission(model_name, operation)
        model = self.env[model_name].with_user(key.user_id).with_company(key.company_id).with_context(
            allowed_company_ids=[key.company_id.id])
        model.check_access(operation)
        return model

    @api.model
    def _field_map(self, model, write=False):
        allowed_types = _WRITE_TYPES if write else _READ_TYPES
        return {name: meta for name, meta in model.fields_get(
            attributes=["string", "type", "readonly", "required"]).items()
            if not name.startswith("_") and not _SENSITIVE.search(name)
            and name not in {"company_id", "company_ids", "id", "display_name", "create_uid", "write_uid"}
            and meta.get("type") in allowed_types and (not write or not meta.get("readonly"))}

    @api.model
    def _selected_fields(self, model, requested):
        catalog = self._field_map(model)
        if requested is None:
            requested = [name for name in ("name", "default_code", "email", "state", "amount_total") if name in catalog]
        if not isinstance(requested, list) or len(requested) > 20 or any(not isinstance(name, str) or name not in catalog for name in requested):
            raise ValidationError("Requested fields are not available for reading.")
        return list(dict.fromkeys(["id", "display_name", *requested]))

    @api.model
    def _values(self, model, values):
        catalog = self._field_map(model, write=True)
        if not isinstance(values, dict) or not values or len(values) > 30 or set(values) - set(catalog):
            raise ValidationError("Values contain an unavailable or read-only field.")
        for name, value in values.items():
            field_type = catalog[name]["type"]
            if isinstance(value, (dict, list)) or (field_type == "many2one" and not (value is False or isinstance(value, int))):
                raise ValidationError("Only simple field values and many2one IDs are supported.")
            if isinstance(value, str) and len(value) > 2000:
                raise ValidationError("A field value is too long.")
        return values

    @api.model
    def _record(self, model, record_id, operation):
        try:
            record_id = int(record_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Record ID must be an integer.") from exc
        if record_id <= 0:
            raise ValidationError("Record ID must be positive.")
        record = model.browse(record_id).exists()
        if not record:
            raise AccessError("Record not found or not available.")
        record.check_access(operation)
        if "company_id" in record._fields and record.company_id and record.company_id.id != model.env.company.id:
            raise AccessError("Record belongs to another company.")
        return record

    @api.model
    def _url(self, model_name, record_id):
        return "/web#id=%s&model=%s&view_type=form" % (record_id, model_name)

    @api.model
    def list_fields(self, key, model_name):
        model = self._model(key, model_name, "read")
        readable = self._field_map(model)
        writable = self._field_map(model, write=True) if key.permits(model_name, "write") else {}
        return {"model": model_name, "fields": [
            {"name": name, "label": meta.get("string") or name, "type": meta["type"],
             "required": bool(meta.get("required")), "writable": name in writable}
            for name, meta in list(readable.items())[:100]]}

    @api.model
    def search_records(self, key, model_name, query="", fields_list=None, limit=10):
        model = self._model(key, model_name, "read")
        selected = self._selected_fields(model, fields_list)
        query = str(query or "").strip()[:80]
        limit = max(1, min(int(limit), 20))
        domain = []
        rec_name = model._rec_name
        if query:
            if rec_name not in self._field_map(model) or model._fields[rec_name].type not in {"char", "text"}:
                raise ValidationError("Text search is not available for this model.")
            domain.append((rec_name, "ilike", query))
        if "company_id" in model._fields:
            domain.append(("company_id", "in", [False, key.company_id.id]))
        records = model.search(domain, limit=limit)
        values = records.read(selected)
        for row in values:
            row["source_url"] = self._url(model_name, row["id"])
        return {"model": model_name, "count": len(values), "records": values}

    @api.model
    def get_record(self, key, model_name, record_id, fields_list=None):
        model = self._model(key, model_name, "read")
        record = self._record(model, record_id, "read")
        row = record.read(self._selected_fields(model, fields_list))[0]
        row["source_url"] = self._url(model_name, record.id)
        return {"model": model_name, "record": row}

    @api.model
    def _once(self, key, operation, arguments, action):
        request_key = arguments.get("request_key") if isinstance(arguments, dict) else None
        if not isinstance(request_key, str) or not 8 <= len(request_key) <= 128:
            raise ValidationError("A request key of 8–128 characters is required for write operations.")
        payload_hash = hashlib.sha256(json.dumps(
            {"operation": operation, "arguments": {k: v for k, v in arguments.items() if k != "request_key"}},
            sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", ["mcp-crud:%s:%s" % (key.id, request_key)])
        ledger = self.env["erpcloud.mcp.center.crud.request"].sudo()
        prior = ledger.search([("key_id", "=", key.id), ("request_key", "=", request_key)], limit=1)
        if prior:
            if prior.payload_hash != payload_hash:
                raise ValidationError("Request key was already used for different content.")
            return prior.result_json
        result = action()
        ledger.create({"key_id": key.id, "request_key": request_key,
                       "payload_hash": payload_hash, "result_json": result})
        return result

    @api.model
    def create_record(self, key, model_name, values, request_key):
        model = self._model(key, model_name, "create")
        values = self._values(model, values)
        def action():
            record = model.create(values)
            return {"model": model_name, "id": record.id, "source_url": self._url(model_name, record.id),
                    "status": "created"}
        return self._once(key, "create", {"model": model_name, "values": values, "request_key": request_key}, action)

    @api.model
    def update_record(self, key, model_name, record_id, values, request_key):
        model = self._model(key, model_name, "write")
        values = self._values(model, values)
        def action():
            record = self._record(model, record_id, "write")
            record.write(values)
            return {"model": model_name, "id": record.id, "source_url": self._url(model_name, record.id),
                    "status": "updated"}
        return self._once(key, "update", {"model": model_name, "id": record_id,
                                           "values": values, "request_key": request_key}, action)

    @api.model
    def delete_record(self, key, model_name, record_id, confirm, request_key):
        model = self._model(key, model_name, "unlink")
        if confirm != "DELETE %s %s" % (model_name, record_id):
            raise ValidationError("Exact record deletion confirmation is required.")
        def action():
            record = self._record(model, record_id, "unlink")
            result = {"model": model_name, "id": record.id, "status": "deleted"}
            record.unlink()
            return result
        return self._once(key, "delete", {"model": model_name, "id": record_id,
                                           "confirm": confirm, "request_key": request_key}, action)
