from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    vn_delivery_address_copy = fields.Char(
        string="Địa chỉ giao hàng để sao chép",
        compute="_compute_vn_delivery_address_copy",
        readonly=True,
        store=False,
    )

    @api.depends(
        "name",
        "street",
        "street2",
        "city",
        "state_id",
        "state_id.name",
        "zip",
        "country_id",
        "country_id.name",
    )
    def _compute_vn_delivery_address_copy(self):
        for partner in self:
            address_parts = (
                partner.street,
                partner.street2,
                partner.city,
                partner.state_id.name,
                partner.zip,
                partner.country_id.name,
            )
            cleaned_address = [part.strip() for part in address_parts if part and part.strip()]
            if cleaned_address:
                name = (partner.name or "").strip()
                partner.vn_delivery_address_copy = ", ".join(
                    ([name] if name else []) + cleaned_address
                )
            else:
                partner.vn_delivery_address_copy = False
