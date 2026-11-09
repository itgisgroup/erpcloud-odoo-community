from odoo.tests.common import TransactionCase


class TestDeliveryAddressCopy(TransactionCase):
    def test_order_and_source_values(self):
        country = self.env["res.country"].create({"name": "Example Country", "code": "XC"})
        state = self.env["res.country.state"].create({
            "name": "Example Province", "code": "XP", "country_id": country.id,
        })
        partner = self.env["res.partner"].create({
            "name": "  Example Company  ", "is_company": True,
            "street": "  12 Main Street ", "street2": " Floor 2 ",
            "city": " Hanoi ", "state_id": state.id,
            "zip": " 10000 ", "country_id": country.id,
        })
        self.assertEqual(
            partner.vn_delivery_address_copy,
            "Example Company, 12 Main Street, Floor 2, Hanoi, Example Province, 10000, Example Country",
        )
        self.assertEqual(partner.street, "  12 Main Street ")
        self.assertEqual(partner.street2, " Floor 2 ")
        self.assertEqual(partner.zip, " 10000 ")

        state.name = "Renamed Province"
        self.assertIn("Renamed Province", partner.vn_delivery_address_copy)
        country.name = "Renamed Country"
        self.assertTrue(partner.vn_delivery_address_copy.endswith("Renamed Country"))

    def test_empty_and_partial_address(self):
        partner = self.env["res.partner"].create({
            "name": "Only a name", "street": "  ", "street2": " ",
            "city": " ", "zip": " ", "state_id": False, "country_id": False,
        })
        self.assertFalse(partner.vn_delivery_address_copy)
        partner.street = "  4 Side Road  "
        self.assertEqual(partner.vn_delivery_address_copy, "Only a name, 4 Side Road")
        partner.name = "  New Name  "
        self.assertEqual(partner.vn_delivery_address_copy, "New Name, 4 Side Road")
        partner.street = False
        partner.zip = " 70000 "
        self.assertEqual(partner.vn_delivery_address_copy, "New Name, 70000")

    def test_each_address_source_recomputes(self):
        partner = self.env["res.partner"].create({
            "name": "Person", "is_company": False, "country_id": False,
        })
        updates = (
            ("street", "A", "Person, A"),
            ("street2", "B", "Person, A, B"),
            ("city", "C", "Person, A, B, C"),
            ("zip", "D", "Person, A, B, C, D"),
        )
        for field, value, expected in updates:
            partner.write({field: value})
            self.assertEqual(partner.vn_delivery_address_copy, expected)
        country = self.env["res.country"].create({"name": "Country Z", "code": "XZ"})
        state = self.env["res.country.state"].create({
            "name": "State Z", "code": "SZ", "country_id": country.id,
        })
        partner.write({"country_id": country.id, "state_id": state.id})
        self.assertEqual(
            partner.vn_delivery_address_copy,
            "Person, A, B, C, State Z, D, Country Z",
        )
        partner.write({"state_id": False, "country_id": False})
        self.assertEqual(partner.vn_delivery_address_copy, "Person, A, B, C, D")
