import re

from odoo import api, fields, models
from odoo.fields import Domain


def vietnam_mobile_key(value):
    """Return a domestic 10-digit mobile number, or False if not recognizable."""
    if not value:
        return False
    if not re.fullmatch(r"[+0-9()\s.\-]+", value):
        return False
    digits = re.sub(r"\D", "", value)
    if digits.startswith("0084"):
        digits = digits[4:]
    elif digits.startswith("84"):
        digits = digits[2:]
    if len(digits) == 9 and digits[0] in "35789":
        digits = "0" + digits
    if len(digits) == 10 and digits[:2] in {"03", "05", "07", "08", "09"}:
        return digits
    return False


class ResPartner(models.Model):
    _inherit = "res.partner"

    vn_phone_key = fields.Char(
        string="Vietnam mobile key (phone)",
        compute="_compute_vn_phone_key",
        store=True,
        index=True,
        copy=False,
    )
    @api.depends("phone", "country_id")
    def _compute_vn_phone_key(self):
        for partner in self:
            is_vietnam = not partner.country_id or partner.country_id.code == "VN"
            partner.vn_phone_key = vietnam_mobile_key(partner.phone) if is_vietnam else False

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if operator not in {"ilike", "like", "="} or not isinstance(value, str):
            return domain
        key = vietnam_mobile_key(value)
        if not key:
            return domain
        return Domain.OR([
            domain,
            Domain("vn_phone_key", "=", key),
        ])
