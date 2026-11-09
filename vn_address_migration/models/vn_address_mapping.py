from odoo import api, fields, models


class VnAddressMapping(models.Model):
    _name = "vn.address.mapping"
    _description = "Vietnam old-to-new ward mapping"
    _order = "old_ward, new_ward, id"

    name = fields.Char(string="Label", compute="_compute_name", store=True)
    old_ward = fields.Char(string="Old ward", required=True)
    old_code = fields.Char(string="Old code")
    new_ward = fields.Char(string="New ward", required=True)
    new_code = fields.Char(string="New code")
    new_province = fields.Char(string="New province")
    new_province_code = fields.Char(string="New province code")
    classification = fields.Selection(
        selection=[
            ("unchanged", "Unchanged"),
            ("renamed", "Renamed"),
            ("merged", "Merged"),
            ("divided", "Divided"),
        ],
        string="Classification",
        required=True,
        default="merged",
    )
    phan = fields.Selection(
        selection=[("full", "Full"), ("partial", "Partial")],
        string="Portion",
        default="full",
    )
    is_default_new_ward = fields.Boolean(string="Default new ward")
    source_resolution = fields.Char(string="Resolution")
    source_clause = fields.Char(string="Clause")
    source_effective_date = fields.Date(string="Effective date")
    source_note = fields.Text(string="Source note")
    active = fields.Boolean(string="Active", default=True)

    @api.depends("old_ward", "new_ward", "new_province")
    def _compute_name(self):
        for rec in self:
            rec.name = "%s → %s" % (rec.old_ward or "?", rec.new_ward or "?")
