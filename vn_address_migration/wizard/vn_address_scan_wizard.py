from odoo import _, fields, models
from odoo.exceptions import UserError


class VnAddressScanWizard(models.TransientModel):
    _name = "vn.address.scan.wizard"
    _description = "Scan contacts for old 3-level Vietnamese addresses"

    partner_ids = fields.Many2many("res.partner", string="Contacts")

    def action_scan(self):
        if not self.partner_ids:
            raise UserError(_("Select at least one contact."))
        migrations = self.env["vn.address.migration"]._scan_partners(self.partner_ids)
        return {
            "type": "ir.actions.act_window",
            "name": _("Address migrations"),
            "res_model": "vn.address.migration",
            "view_mode": "tree,form",
            "domain": [("id", "in", migrations.ids)],
            "context": {"create": False},
        }
