import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VnAddressMigration(models.Model):
    _name = "vn.address.migration"
    _description = "Vietnam address migration proposal (review queue + audit)"
    _order = "create_date desc, id desc"

    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("review", "Review"),
            ("applied", "Applied"),
            ("skipped", "Skipped"),
        ],
        string="Status",
        required=True,
        default="draft",
    )
    kind = fields.Selection(
        selection=[
            ("direct", "Direct"),
            ("divided", "Divided"),
            ("ambiguous", "Ambiguous"),
            ("unmatched", "Unmatched"),
        ],
        string="Kind",
        required=True,
    )
    old_street = fields.Char(string="Old street")
    old_street2 = fields.Char(string="Old street 2")
    old_city = fields.Char(string="Old city")
    old_state_id = fields.Many2one("res.country.state", string="Old state")
    old_country_id = fields.Many2one("res.country", string="Old country")
    old_zip = fields.Char(string="Old ZIP")
    new_street = fields.Char(string="New street")
    new_street2 = fields.Char(string="New street 2")
    new_city = fields.Char(string="New city")
    new_state_id = fields.Many2one("res.country.state", string="New state")
    new_country_id = fields.Many2one("res.country", string="New country")
    new_zip = fields.Char(string="New ZIP")
    mapping_id = fields.Many2one("vn.address.mapping", string="Applied mapping")
    candidate_mapping_ids = fields.Many2many(
        "vn.address.mapping", "vn_address_migration_mapping_rel",
        "migration_id", "mapping_id", string="Candidates",
    )
    reason = fields.Text(string="Reason")
    applied_uid = fields.Many2one("res.users", string="Applied by")
    applied_date = fields.Datetime(string="Applied on")
    active = fields.Boolean(string="Active", default=True)

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize(value):
        """Lowercase, strip diacritics, drop the unit-type prefix."""
        if not value:
            return ""
        text = (value or "").lower().replace("đ", "d")
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = text.strip()
        for prefix in (
            "xa ", "phuong ", "thi tran ", "thi xa ", "quan ",
            "huyen ", "dac khu ", "thanh pho ", "tp ",
        ):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        return " ".join(text.split())

    @staticmethod
    def _contains_word(haystack, word):
        """True when ``word`` appears in ``haystack`` as a whole token."""
        if not word or not haystack:
            return False
        length = len(word)
        idx = haystack.find(word)
        while idx != -1:
            before = haystack[idx - 1] if idx > 0 else " "
            after = haystack[idx + length] if idx + length < len(haystack) else " "
            if not before.isalnum() and not after.isalnum():
                return True
            idx = haystack.find(word, idx + 1)
        return False

    @api.model
    def _group_mappings(self):
        """Return {normalized_old_ward: recordset} for every active mapping."""
        mapping_model = self.env["vn.address.mapping"]
        groups = {}
        for row in mapping_model.search([("active", "=", True)]):
            key = self._normalize(row.old_ward)
            if len(key) < 3:
                continue
            groups.setdefault(key, mapping_model.browse())
            groups[key] |= row
        return groups

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------
    @api.model
    def _scan_partners(self, partners):
        groups = self._group_mappings()
        created = self.env["vn.address.migration"]
        for partner in partners:
            created |= self._scan_partner(partner, groups)
        return created

    @api.model
    def _scan_partner(self, partner, groups=None):
        if groups is None:
            groups = self._group_mappings()
        haystack = self._normalize(" ".join(
            part for part in (partner.street, partner.street2, partner.city)
            if part
        ))
        matched = [rows for _key, rows in groups.items()
                   if self._contains_word(haystack, _key)]
        if not matched:
            return self._create_migration(
                partner, kind="unmatched", state="review",
                reason=_("No matching old ward found in the contact address."),
            )
        candidates = self.env["vn.address.mapping"]
        for rows in matched:
            candidates |= rows
        if len(matched) == 1 and len(matched[0]) == 1:
            row = matched[0]
            return self._create_migration(
                partner, kind="direct", state="draft", mapping=row,
                reason=self._build_reason(row),
            )
        kind = "divided" if len(matched) == 1 else "ambiguous"
        default = next((r for r in candidates if r.is_default_new_ward), candidates[0])
        return self._create_migration(
            partner, kind=kind, state="review", mapping=default,
            candidates=candidates,
            reason=_("Multiple destinations for the old ward; choose one in the review queue."),
        )

    @staticmethod
    def _build_reason(row):
        labels = {
            "unchanged": _("Unchanged"),
            "renamed": _("Renamed"),
            "merged": _("Merged"),
            "divided": _("Divided"),
        }
        parts = [labels.get(row.classification, row.classification or "")]
        if row.source_resolution:
            parts.append(row.source_resolution)
        if row.new_province:
            parts.append(_("Province: %s") % row.new_province)
        return " · ".join(parts)

    @api.model
    def _resolve_state(self, province_name):
        if not province_name:
            return self.env["res.country.state"].browse()
        return self.env["res.country.state"].search(
            [("name", "=ilike", province_name)], limit=1,
        )

    @api.model
    def _create_migration(self, partner, kind, state, mapping=None, candidates=None, reason=""):
        default = mapping or (candidates[:1] if candidates else self.env["vn.address.mapping"].browse())
        new_state = self._resolve_state(default.new_province) if default else self.env["res.country.state"].browse()
        vals = {
            "partner_id": partner.id,
            "kind": kind,
            "state": state,
            "old_street": partner.street,
            "old_street2": partner.street2,
            "old_city": partner.city,
            "old_state_id": partner.state_id.id,
            "old_country_id": partner.country_id.id,
            "old_zip": partner.zip,
            "new_city": default.new_ward if default else False,
            "new_state_id": new_state.id if new_state else False,
            "mapping_id": default.id if default else False,
            "candidate_mapping_ids": [(6, 0, candidates.ids)] if candidates else False,
            "reason": reason,
        }
        return self.env["vn.address.migration"].create(vals)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_apply(self):
        self.ensure_one()
        self.check_access("write")
        if self.state == "applied":
            raise UserError(_("This migration is already applied."))
        if self.state == "skipped":
            raise UserError(_("A skipped migration cannot be applied."))
        if self.kind == "unmatched":
            raise UserError(_("No destination is known for this address; set one manually before applying."))
        if self.kind == "review" and not self.mapping_id:
            raise UserError(_("Choose a destination ward before applying."))
        partner = self.partner_id
        partner.check_access("write")
        write_vals = {}
        if self.new_city:
            write_vals["city"] = self.new_city
        if self.new_state_id:
            write_vals["state_id"] = self.new_state_id.id
        if not write_vals:
            raise UserError(_("No destination value is set on this migration."))
        partner.write(write_vals)
        self.write({
            "state": "applied",
            "applied_uid": self.env.uid,
            "applied_date": fields.Datetime.now(),
        })

    def action_skip(self):
        for rec in self:
            if rec.state == "applied":
                raise UserError(_("An applied migration cannot be skipped."))
            rec.state = "skipped"

    def unlink(self):
        raise UserError(_(
            "Migration records keep the audit trail and cannot be deleted. "
            "Archive them instead."
        ))
