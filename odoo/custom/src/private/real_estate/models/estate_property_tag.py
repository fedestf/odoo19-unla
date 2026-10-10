from odoo import fields, models


class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Etiqueta de propiedad"

    name = fields.Char(string="Nombre", required=True)
