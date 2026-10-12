from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Propiedad"

    name = fields.Char(string="Título", required=True)
    description = fields.Text(string="Descripción")
    postcode = fields.Char(string="Código Postal")
    date_availability = fields.Date(
        string="Fecha disponibilidad",
        copy=False,
        default=lambda self: fields.Date.add(fields.Date.context_today(self), months=3),
    )
    expected_price = fields.Float(string="Precio esperado")
    selling_price = fields.Float(string="Precio de venta", copy=False)
    bedrooms = fields.Integer(string="Habitaciones", default=2)
    living_area = fields.Integer(string="Superficie cubierta")
    facades = fields.Integer(string="Fachadas")
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Jardín")
    garden_orientation = fields.Selection(
        selection=[
            ("north", "Norte"),
            ("south", "Sur"),
            ("east", "Este"),
            ("west", "Oeste"),
        ],
        default="north",
        string="Orientación del jardín",
    )
    garden_area = fields.Integer(string="Superficie jardín")
    state = fields.Selection(
        selection=[
            ("new", "Nuevo"),
            ("offer_received", "Oferta recibida"),
            ("offer_accepted", "Oferta aceptada"),
            ("sold", "Vendido"),
            ("canceled", "Cancelado"),
        ],
        string="Estado",
        required=True,
        default="new",
        copy=False,
    )
    property_type_id = fields.Many2one(
        comodel_name="estate.property.type",
        string="Tipo Propiedad",
    )
    buyer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Comprador",
    )
    salesman_id = fields.Many2one(
        comodel_name="res.users",
        string="Vendedor",
        copy=False,
        default=lambda self: self.env.user,
    )
    tag_ids = fields.Many2many(
        comodel_name="estate.property.tag",
        string="Etiquetas",
    )
    offer_ids = fields.One2many(
        comodel_name="estate.property.offer",
        inverse_name="property_id",
        string="Ofertas",
    )

    total_area = fields.Integer(
        string="Superficie total",
        compute="_compute_total_area",
        store=True,
    )

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for property_record in self:
            property_record.total_area = (
                property_record.living_area + property_record.garden_area
            )

    best_offer = fields.Float(
        string="Mejor oferta",
        compute="_compute_best_offer",
    )

    @api.depends("offer_ids.price")
    def _compute_best_offer(self):
        for property_record in self:
            property_record.best_offer = max(
                property_record.offer_ids.mapped("price"), default=0.0
            )

    @api.onchange("garden")
    def _onchange_garden(self):
        for property_record in self:
            property_record.garden_area = 10 if property_record.garden else 0

    @api.onchange("expected_price")
    def _onchange_expected_price(self):
        if self.expected_price < 10000:
            return {
                "warning": {
                    "title": _("Precio esperado bajo"),
                    "message": _(
                        "El precio esperado es menor que 10.000. "
                        "Revisá el importe por si hubo un error de tipeo."
                    ),
                }
            }

    def action_cancel(self):
        if any(property_record.state == "sold" for property_record in self):
            raise UserError(_("No se puede cancelar una propiedad vendida."))
        self.write({"state": "canceled"})
        return True

    def action_sold(self):
        if any(property_record.state == "canceled" for property_record in self):
            raise UserError(_("No se puede marcar como vendida una propiedad cancelada."))
        self.write({"state": "sold"})
        return True
