from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        result = super()._post(soft=soft)
        self.env['ep.commission.entry'].sudo()._sync_moves(self.filtered(lambda m: m.state == 'posted'))
        return result

    def _invoice_paid_hook(self):
        result = super()._invoice_paid_hook()
        self.env['ep.commission.entry'].sudo()._sync_moves(self)
        return result

    def button_draft(self):
        posted = self.filtered(lambda move: move.state == 'posted')
        result = super().button_draft()
        self.env['ep.commission.entry'].sudo()._reverse_moves(posted)
        return result
