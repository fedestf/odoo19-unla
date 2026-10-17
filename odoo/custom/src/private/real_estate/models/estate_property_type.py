from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Tipo de propiedad"

    _unique_type_name = models.Constraint(
        "UNIQUE(name)", "El nombre del tipo de propiedad debe ser único."
    )

    name = fields.Char(string="Nombre", required=True)
