from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..protocol.engine import MCPProtocolEngine, MCPSession


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

    def test_quote_preview_approval_and_idempotency(self):
        key, _secret = self.key_model.issue("Test quote key", scope="quote")
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
