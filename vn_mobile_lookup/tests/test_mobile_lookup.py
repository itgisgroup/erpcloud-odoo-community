from odoo.tests.common import TransactionCase

from ..models.res_partner import vietnam_mobile_key


class TestVietnamMobileLookup(TransactionCase):
    def test_normalization(self):
        self.assertEqual(vietnam_mobile_key("0912 345 678"), "0912345678")
        self.assertEqual(vietnam_mobile_key("+84-912-345-678"), "0912345678")
        self.assertEqual(vietnam_mobile_key("0084 912 345 678"), "0912345678")
        self.assertFalse(vietnam_mobile_key("028 1234 5678"))
        self.assertFalse(vietnam_mobile_key("0912 345 678 ext 2"))
        self.assertFalse(vietnam_mobile_key("call 0912 345 678"))

    def test_lookup_and_recompute(self):
        partner = self.env["res.partner"].create({
            "name": "Mobile lookup sample",
            "phone": "+84 912 345 678",
        })
        self.assertEqual(partner.vn_phone_key, "0912345678")
        for query in ("0912345678", "+84 912 345 678", "0084 912 345 678"):
            self.assertIn(partner.id, self.env["res.partner"].search([
                ("display_name", "ilike", query),
            ]).ids)
            self.assertIn(partner.id, [record_id for record_id, _name in
                self.env["res.partner"].name_search(query)])
        partner.phone = "0388 123 456"
        self.assertEqual(partner.vn_phone_key, "0388123456")
        self.assertNotIn(partner.id, self.env["res.partner"].search([
            ("display_name", "ilike", "0912345678"),
        ]).ids)
        self.assertIn(partner.id, self.env["res.partner"].search([
            ("display_name", "ilike", "0388123456"),
        ]).ids)

    def test_country_and_domain_are_respected(self):
        us = self.env.ref("base.us")
        partner = self.env["res.partner"].create({
            "name": "Foreign contact",
            "country_id": us.id,
            "phone": "0912 345 678",
        })
        self.assertFalse(partner.vn_phone_key)
        partner.country_id = self.env.ref("base.vn")
        self.assertEqual(partner.vn_phone_key, "0912345678")
        matches = self.env["res.partner"].name_search(
            "0912345678", domain=[("id", "!=", partner.id)]
        )
        self.assertNotIn(partner.id, [record_id for record_id, _name in matches])
