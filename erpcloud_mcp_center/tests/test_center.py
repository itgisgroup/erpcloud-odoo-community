from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..protocol.engine import MCPProtocolEngine, MCPSession
from ..controllers.mcp import _tools


@tagged("post_install", "-at_install")
class TestMCPCenter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = cls.env.ref("base.user_admin")
        cls.partner = cls.env["res.partner"].create({"name": "MCP Test Buyer"})
        cls.product = cls.env["product.product"].create({
            "name": "MCP Test Product", "list_price": 125.0,
            "taxes_id": [(5, 0, 0)],
        })
        cls.key_model = cls.env["erpcloud.mcp.center.key"].with_user(cls.owner)
        cls.proposal_model = cls.env["erpcloud.mcp.center.proposal"].with_user(cls.owner)

    def test_key_is_hashed_scoped_and_revocable(self):
        key, secret = self.key_model.issue("Test read key")
        self.assertEqual(key.scope, "read")
        self.assertNotEqual(key.secret_hash, secret)
        self.assertEqual(self.key_model.authenticate(secret), key)
        self.assertFalse(self.key_model.authenticate("wrong"))
        with self.assertRaises(AccessError):
            self.proposal_model.propose(key, {"partner_id": self.partner.id, "lines": []}, "same-request-key")
        key.revoke_for_actor()
        self.assertFalse(self.key_model.authenticate(secret))

    def test_model_permissions_hide_tools_and_block_direct_calls(self):
        key, _secret = self.key_model.issue("Customer lookup only", permissions={"res.partner": ["lookup"]})
        self.assertEqual([tool["name"] for tool in _tools(key, True)], ["whoami", "customer_lookup"])
        self.assertTrue(key.permits("res.partner", "lookup"))
        self.assertFalse(key.permits("sale.order", "briefing"))
        with self.assertRaises(AccessError):
            key.require_permission("product.product", "lookup")
        with self.assertRaises(ValidationError):
            self.key_model.issue("Unsafe model", permissions={"res.users": ["lookup"]})
        with self.assertRaises(AccessError):
            self.key_model.issue("Unsafe operation", permissions={"sale.order": ["propose"]})

    def test_dynamic_model_catalog_and_crud_with_idempotency(self):
        gateway = self.env["erpcloud.mcp.center.gateway"]
        self.assertTrue(any(item["model"] == "res.partner" for item in gateway.catalog(query="res.partner")))
        with self.assertRaises(AccessError):
            self.key_model.issue("Read scope cannot write", permissions={"res.partner": ["read", "create"]})
        key, _secret = self.key_model.issue("Partner CRUD", scope="write", permissions={
            "res.partner": ["read", "create", "write", "unlink"]})
        names = [tool["name"] for tool in _tools(key, True)]
        self.assertTrue({"list_models", "get_fields", "search_records", "get_record",
                         "create_record", "update_record", "delete_record"} <= set(names))
        self.assertNotIn("create_record", [tool["name"] for tool in _tools(key, False)])
        fields = gateway.list_fields(key, "res.partner")["fields"]
        self.assertTrue(any(item["name"] == "name" for item in fields))
        first = gateway.create_record(key, "res.partner", {"name": "MCP Dynamic Buyer"}, "dynamic-create-1")
        self.assertEqual(first, gateway.create_record(key, "res.partner", {"name": "MCP Dynamic Buyer"}, "dynamic-create-1"))
        self.assertEqual(self.env["res.partner"].search_count([("name", "=", "MCP Dynamic Buyer")]), 1)
        self.assertEqual(gateway.get_record(key, "res.partner", first["id"], ["name"])["record"]["name"], "MCP Dynamic Buyer")
        self.assertEqual(gateway.search_records(key, "res.partner", "MCP Dynamic", ["name"])["count"], 1)
        with self.assertRaises(ValidationError):
            gateway.create_record(key, "res.partner", {"name": "Other"}, "dynamic-create-1")
        with self.assertRaises(ValidationError):
            gateway.update_record(key, "res.partner", first["id"], {"company_id": self.env.company.id}, "dynamic-update-1")
        updated = gateway.update_record(key, "res.partner", first["id"], {"name": "Updated Buyer"}, "dynamic-update-2")
        self.assertEqual(updated["status"], "updated")
        with self.assertRaises(ValidationError):
            gateway.delete_record(key, "res.partner", first["id"], "DELETE", "dynamic-delete-1")
        deleted = gateway.delete_record(key, "res.partner", first["id"],
                                        "DELETE res.partner %s" % first["id"], "dynamic-delete-2")
        self.assertEqual(deleted, gateway.delete_record(key, "res.partner", first["id"],
                                                        "DELETE res.partner %s" % first["id"], "dynamic-delete-2"))
        self.assertFalse(self.env["res.partner"].browse(first["id"]).exists())

    def test_dynamic_permissions_are_model_specific(self):
        gateway = self.env["erpcloud.mcp.center.gateway"]
        key, _secret = self.key_model.issue("Only partner read", permissions={"res.partner": ["read"]})
        with self.assertRaises(AccessError):
            gateway.search_records(key, "product.product", "MCP")
        with self.assertRaises(AccessError):
            gateway.create_record(key, "res.partner", {"name": "Denied"}, "denied-create-1")
        with self.assertRaises(ValidationError):
            self.key_model.issue("Invalid model", permissions={"erpcloud.mcp.center.key": ["read"]})

    def test_dynamic_company_boundary_and_sensitive_fields(self):
        gateway = self.env["erpcloud.mcp.center.gateway"]
        foreign_company = self.env["res.company"].create({"name": "MCP Foreign Company"})
        foreign_partner = self.env["res.partner"].create({
            "name": "Foreign MCP Buyer", "company_id": foreign_company.id})
        key, _secret = self.key_model.issue("Partner read", permissions={"res.partner": ["read"]})
        with self.assertRaises(AccessError):
            gateway.get_record(key, "res.partner", foreign_partner.id, ["name"])
        self.assertFalse(gateway.search_records(key, "res.partner", "Foreign MCP Buyer")["records"])
        user_key, _secret = self.key_model.issue("User read", permissions={"res.users": ["read"]})
        available = {row["name"] for row in gateway.list_fields(user_key, "res.users")["fields"]}
        self.assertFalse(any("password" in field or "token" in field for field in available))

    def test_quotation_permission_is_separate_from_quote_scope(self):
        key, _secret = self.key_model.issue("Quote scope without proposal", scope="quote",
                                            permissions={"sale.order": ["briefing"]})
        self.assertNotIn("quotation_propose", [tool["name"] for tool in _tools(key, True)])
        with self.assertRaises(AccessError):
            self.proposal_model.propose(key, {"partner_id": self.partner.id,
                "lines": [{"product_id": self.product.id, "quantity": 1}]}, "no-propose-permission")
        key.model_permissions = False
        self.assertTrue(key.permits("sale.order", "propose"))

    def test_quote_preview_approval_and_idempotency(self):
        key, _secret = self.key_model.issue("Test quote key", scope="quote")
        self.assertNotIn("quotation_propose", [tool["name"] for tool in _tools(key, False)])
        inputs = {"partner_id": self.partner.id,
                  "lines": [{"product_id": self.product.id, "quantity": 2}],
                  "note": "Human review required"}
        proposal = self.proposal_model.propose(key, inputs, "test-request-12345")
        self.assertEqual(self.proposal_model.propose(key, inputs, "test-request-12345"), proposal)
        self.assertEqual(proposal.state, "pending")
        self.assertEqual(proposal.preview_json["partner_id"], self.partner.id)
        self.assertAlmostEqual(proposal.preview_json["amount_total"], 250.0, places=2)
        with self.assertRaises(ValidationError):
            self.proposal_model.propose(key, {**inputs, "note": "Changed"}, "test-request-12345")
        order = proposal.decide(True)
        self.assertEqual(order.state, "draft")
        self.assertEqual(proposal.state, "approved")
        self.assertEqual(proposal.decide(True), order)
        self.assertEqual(order.partner_id, self.partner)
        self.assertAlmostEqual(order.amount_total, 250.0, places=2)

    def test_reject_creates_no_sale_order(self):
        key, _secret = self.key_model.issue("Test reject key", scope="quote")
        proposal = self.proposal_model.propose(key, {
            "partner_id": self.partner.id,
            "lines": [{"product_id": self.product.id, "quantity": 1}],
        }, "test-reject-12345")
        before = self.env["sale.order"].search_count([])
        self.assertFalse(proposal.decide(False))
        self.assertEqual(proposal.state, "rejected")
        self.assertEqual(self.env["sale.order"].search_count([]), before)

    def test_quote_key_cannot_be_used_as_another_user(self):
        key, _secret = self.key_model.issue("Owner only", scope="quote")
        other = self.env["res.users"].create({
            "name": "MCP Other User", "login": "mcp.other.user.qa",
            "company_ids": [(6, 0, [self.owner.company_id.id])],
            "company_id": self.owner.company_id.id,
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            self.proposal_model.with_user(other).propose(key, {
                "partner_id": self.partner.id,
                "lines": [{"product_id": self.product.id, "quantity": 1}],
            }, "cross-user-denied-123")

    def test_price_change_requires_new_preview(self):
        key, _secret = self.key_model.issue("Price drift", scope="quote")
        proposal = self.proposal_model.propose(key, {
            "partner_id": self.partner.id,
            "lines": [{"product_id": self.product.id, "quantity": 1}],
        }, "price-drift-denied-123")
        self.product.list_price = 140.0
        with self.assertRaises(ValidationError):
            proposal.decide(True)
        self.assertEqual(proposal.state, "pending")
        self.assertFalse(proposal.sale_order_id)

    def test_other_company_product_is_rejected(self):
        second_company = self.env["res.company"].create({"name": "MCP Isolated Company"})
        foreign_product = self.env["product.product"].create({
            "name": "Not for this company", "company_id": second_company.id,
            "list_price": 99.0,
        })
        key, _secret = self.key_model.issue("Company boundary", scope="quote")
        with self.assertRaises(AccessError):
            self.proposal_model.propose(key, {
                "partner_id": self.partner.id,
                "lines": [{"product_id": foreign_product.id, "quantity": 1}],
            }, "company-boundary-123")

    def test_protocol_lifecycle(self):
        engine = MCPProtocolEngine(lambda _session, _params: {"tools": []}, lambda _session, _name, _args: {"ok": True})
        session = MCPSession("unit-test", self.owner.id)
        init = engine.dispatch(session, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                         "params": {"protocolVersion": "2025-06-18", "clientInfo": {"name": "test", "version": "1"}}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-06-18")
        self.assertIsNone(engine.dispatch(session, {"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(engine.dispatch(session, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"], {"tools": []})
