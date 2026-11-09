from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestVnAddressMigration(TransactionCase):
    def setUp(self):
        super().setUp()
        # Deactivate shipped sample rows so each test starts with a clean mapping.
        self.env["vn.address.mapping"].search([]).write({"active": False})
        self.country = self.env["res.country"].search([("code", "=", "VN")], limit=1)
        if not self.country:
            self.country = self.env["res.country"].create({"name": "Vietnam", "code": "VN"})
        self.state_hn = self.env["res.country.state"].search([
            ("code", "=", "VN-HN"), ("country_id", "=", self.country.id),
        ], limit=1)
        if not self.state_hn:
            self.state_hn = self.env["res.country.state"].create({
                "name": "Hà Nội", "code": "VN-HN", "country_id": self.country.id,
            })
        self.mapping = self.env["vn.address.mapping"]

    def _mapping(self, **kw):
        return self.mapping.create(kw)

    def _partner(self, **kw):
        vals = {"name": "Test Contact", "country_id": self.country.id}
        vals.update(kw)
        return self.env["res.partner"].create(vals)

    def _scan(self, partner):
        return self.env["vn.address.migration"]._scan_partners(partner)

    def test_merged_direct_no_overwrite_until_apply(self):
        m = self._mapping(
            old_ward="Phúc Xá", new_ward="Hồng Hà", new_province="Hà Nội",
            classification="merged", phan="full",
        )
        partner = self._partner(city="Phúc Xá", street="12 Láng Hạ", state_id=self.state_hn.id)
        mig = self._scan(partner)
        self.assertEqual(len(mig), 1)
        self.assertEqual(mig.kind, "direct")
        self.assertEqual(mig.state, "draft")
        self.assertEqual(mig.mapping_id, m)
        self.assertEqual(mig.old_city, "Phúc Xá")
        self.assertEqual(mig.new_city, "Hồng Hà")
        self.assertEqual(mig.new_state_id.name, "Hà Nội")
        # source untouched before explicit apply
        self.assertEqual(partner.city, "Phúc Xá")
        self.assertEqual(partner.street, "12 Láng Hạ")

        mig.action_apply()
        self.assertEqual(partner.city, "Hồng Hà")
        self.assertEqual(mig.state, "applied")
        self.assertTrue(mig.applied_date)
        self.assertEqual(mig.applied_uid, self.env.user)
        # audit keeps old and new values
        self.assertEqual(mig.old_city, "Phúc Xá")
        self.assertEqual(mig.new_city, "Hồng Hà")

    def test_divided_review_default_and_choice(self):
        m1 = self._mapping(
            old_ward="Cống Vị", new_ward="Ngọc Hà", new_province="Hà Nội",
            classification="divided", phan="partial", is_default_new_ward=True,
        )
        m2 = self._mapping(
            old_ward="Cống Vị", new_ward="Giảng Võ", new_province="Hà Nội",
            classification="divided", phan="partial", is_default_new_ward=False,
        )
        partner = self._partner(city="Cống Vị", state_id=self.state_hn.id)
        mig = self._scan(partner)
        self.assertEqual(mig.kind, "divided")
        self.assertEqual(mig.state, "review")
        self.assertIn(m1, mig.candidate_mapping_ids)
        self.assertIn(m2, mig.candidate_mapping_ids)
        self.assertEqual(mig.mapping_id, m1)  # default flagged new ward
        self.assertEqual(partner.city, "Cống Vị")  # source unchanged

        # choose the non-default destination then apply
        mig.mapping_id = m2
        mig.action_apply()
        self.assertEqual(partner.city, "Giảng Võ")
        self.assertEqual(mig.state, "applied")

    def test_ambiguous_goes_to_review(self):
        self._mapping(
            old_ward="Ba Đình", new_ward="Ba Đình", new_province="Hà Nội",
            classification="unchanged", phan="full",
        )
        self._mapping(
            old_ward="Láng Hạ", new_ward="Láng Hạ", new_province="Hà Nội",
            classification="unchanged", phan="full",
        )
        partner = self._partner(city="Ba Đình", street="Láng Hạ")
        mig = self._scan(partner)
        self.assertEqual(len(mig), 1)
        self.assertEqual(mig.kind, "ambiguous")
        self.assertEqual(mig.state, "review")

    def test_unmatched_review_and_cannot_apply(self):
        partner = self._partner(city="Địa chỉ không xác định")
        mig = self._scan(partner)
        self.assertEqual(mig.kind, "unmatched")
        self.assertEqual(mig.state, "review")
        self.assertFalse(mig.mapping_id)
        with self.assertRaises(UserError):
            mig.action_apply()

    def test_normalization_diacritics_and_prefix(self):
        self._mapping(
            old_ward="Phúc Xá", new_ward="Hồng Hà", new_province="Hà Nội",
            classification="merged", phan="full",
        )
        partner = self._partner(city="Xã PHÚC XÁ")
        mig = self._scan(partner)
        self.assertEqual(mig.kind, "direct")
        self.assertEqual(mig.new_city, "Hồng Hà")

    def test_audit_trail_and_no_unlink(self):
        m = self._mapping(
            old_ward="Phúc Xá", new_ward="Hồng Hà", new_province="Hà Nội",
            classification="merged", phan="full",
            source_resolution="1656/NQ-UBTVQH15",
        )
        partner = self._partner(city="Phúc Xá")
        mig = self._scan(partner)
        self.assertEqual(mig.create_uid, self.env.user)
        mig.action_apply()
        self.assertEqual(mig.state, "applied")
        self.assertEqual(mig.applied_uid, self.env.user)
        self.assertEqual(mig.mapping_id, m)
        self.assertEqual(mig.mapping_id.source_resolution, "1656/NQ-UBTVQH15")
        with self.assertRaises(UserError):
            mig.unlink()

    def test_permission_non_manager_cannot_apply(self):
        self._mapping(
            old_ward="Phúc Xá", new_ward="Hồng Hà", new_province="Hà Nội",
            classification="merged", phan="full",
        )
        partner = self._partner(city="Phúc Xá")
        mig = self._scan(partner)
        user = self.env["res.users"].create({
            "name": "Plain User",
            "login": "plain_user_%s" % self.env.cr.dbname,
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            mig.with_user(user).action_apply()
        self.assertEqual(partner.city, "Phúc Xá")
        self.assertEqual(mig.state, "draft")

    def test_permission_manager_can_apply(self):
        self._mapping(
            old_ward="Phúc Xá", new_ward="Hồng Hà", new_province="Hà Nội",
            classification="merged", phan="full",
        )
        partner = self._partner(city="Phúc Xá")
        mig = self._scan(partner)
        user = self.env["res.users"].create({
            "name": "Manager User",
            "login": "manager_user_%s" % self.env.cr.dbname,
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("vn_address_migration.group_vn_address_migration_manager").id,
                self.env.ref("base.group_partner_manager").id,
            ])],
        })
        mig.with_user(user).action_apply()
        self.assertEqual(mig.state, "applied")
        self.assertEqual(partner.city, "Hồng Hà")
