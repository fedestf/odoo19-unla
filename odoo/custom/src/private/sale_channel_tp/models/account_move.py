from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_channel_id = fields.Many2one(
        'sale.channel.tp', string='Canal de venta', readonly=True,
        check_company=True, ondelete='restrict', index=True,
        help='Canal trasladado desde el pedido de venta. Las facturas manuales pueden no tener canal.',
    )

    @api.constrains('sale_channel_id', 'journal_id', 'company_id', 'move_type')
    def _check_sale_channel_journal(self):
        for move in self:
            if move.sale_channel_id:
                if move.move_type not in ('out_invoice', 'out_refund'):
                    raise ValidationError(_('El canal de venta solo corresponde a facturas o notas de crédito de clientes.'))
                if (move.sale_channel_id.company_id != move.company_id
                        or move.journal_id != move.sale_channel_id.journal_id):
                    raise ValidationError(_('La factura debe usar la compañía y el diario de su canal de venta.'))
