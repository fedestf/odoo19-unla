from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Oferta sobre propiedad"

    _unique_partner_property = models.Constraint(
        "UNIQUE(partner_id, property_id)",
        "Un mismo ofertante solo puede tener una oferta por propiedad.",
    )

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

    def action_accept(self):
        self.ensure_one()
        property_record = self.property_id
        if property_record.state in ("sold", "canceled"):
            raise UserError(_("No se puede aceptar una oferta de una propiedad vendida o cancelada."))
        other_offers = property_record.offer_ids - self
        other_offers.write({"status": "refused"})
        self.write({"status": "accepted"})
        property_record.write({
            "buyer_id": self.partner_id.id,
            "selling_price": self.price,
            "state": "offer_accepted",
        })
        return True

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(values) for values in vals_list]
        default_property = self.default_get(["property_id"]).get("property_id")
        maxima = {}
        properties = self.env["estate.property"]
        for values in vals_list:
            property_id = values.get("property_id") or default_property
            property_record = self.env["estate.property"].browse(property_id).exists()
            if not property_record:
                raise UserError(_("La oferta debe estar vinculada a una propiedad existente."))
            property_record.check_access("write")
            if property_record.state not in ("new", "offer_received"):
                raise UserError(_("Solo se pueden crear ofertas para propiedades nuevas o con ofertas recibidas."))
            previous = maxima.get(property_record.id, property_record.best_offer)
            price = float(values.get("price", 0.0))
            if price <= previous:
                raise UserError(_("La nueva oferta debe superar la mejor oferta actual: %(price)s.", price=previous))
            values["property_id"] = property_record.id
            maxima[property_record.id] = price
            properties |= property_record
        offers = super().create(vals_list)
        properties.write({"state": "offer_received"})
        return offers
