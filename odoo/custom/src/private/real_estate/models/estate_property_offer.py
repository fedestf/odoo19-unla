from odoo import api, fields, models


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Oferta sobre propiedad"

    price = fields.Float(string="Precio", required=True)
    status = fields.Selection(
        selection=[
            ("accepted", "Aceptada"),
            ("refused", "Rechazada"),
        ],
        string="Estado",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Ofertante",
        required=True,
    )
    property_id = fields.Many2one(
        comodel_name="estate.property",
        string="Propiedad",
        required=True,
    )

    validity = fields.Integer(string="Validez (días)", default=7)
    date_deadline = fields.Date(
        string="Fecha límite",
        compute="_compute_date_deadline",
        inverse="_inverse_date_deadline",
    )

    def _get_deadline_base_date(self):
        self.ensure_one()
        return fields.Date.to_date(self.create_date) or fields.Date.context_today(self)

    @api.depends("create_date", "validity")
    def _compute_date_deadline(self):
        for offer in self:
            offer.date_deadline = fields.Date.add(
                offer._get_deadline_base_date(), days=offer.validity
            )

    def _inverse_date_deadline(self):
        for offer in self:
            if offer.date_deadline:
                offer.validity = (
                    offer.date_deadline - offer._get_deadline_base_date()
                ).days

    property_type_id = fields.Many2one(
        comodel_name="estate.property.type",
        string="Tipo Propiedad",
        related="property_id.property_type_id",
        store=True,
    )
