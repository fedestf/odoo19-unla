from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_channel_id = fields.Many2one(
        related='sale_id.sale_channel_id', string='Canal de venta',
        store=True, readonly=True, index=True,
    )
