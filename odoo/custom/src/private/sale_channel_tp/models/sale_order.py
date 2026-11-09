from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_channel_id = fields.Many2one(
        'sale.channel.tp', string='Canal de venta', required=True,
        check_company=True, ondelete='restrict', index=True,
        domain="[('company_id', '=', company_id)]",
    )

    @api.depends('user_id', 'company_id', 'sale_channel_id', 'sale_channel_id.warehouse_id')
    def _compute_warehouse_id(self):
        super()._compute_warehouse_id()
        for order in self:
            if order.sale_channel_id:
                order.warehouse_id = order.sale_channel_id.warehouse_id

    @api.depends('sale_channel_id', 'sale_channel_id.journal_id')
    def _compute_journal_id(self):
        super()._compute_journal_id()
        for order in self:
            if order.sale_channel_id:
                order.journal_id = order.sale_channel_id.journal_id

    @api.constrains('sale_channel_id', 'warehouse_id', 'journal_id', 'company_id')
    def _check_sale_channel_configuration(self):
        for order in self:
            channel = order.sale_channel_id
            if not channel:
                raise ValidationError(_('Seleccione un canal de venta.'))
            if channel.company_id != order.company_id:
                raise ValidationError(_('El canal debe pertenecer a la compañía del pedido.'))
            if order.warehouse_id != channel.warehouse_id:
                raise ValidationError(_('El depósito del pedido debe ser el del canal seleccionado.'))
            if order.journal_id != channel.journal_id:
                raise ValidationError(_('El diario del pedido debe ser el del canal seleccionado.'))

    def write(self, vals):
        if 'sale_channel_id' in vals:
            for order in self:
                if (order.state not in ('draft', 'sent')
                        and vals['sale_channel_id'] != order.sale_channel_id.id):
                    raise UserError(_('El canal solo puede cambiarse en un presupuesto sin confirmar.'))
                if (vals['sale_channel_id'] != order.sale_channel_id.id
                        and (order.picking_ids or order.invoice_ids)):
                    raise UserError(_('No se puede cambiar el canal de un pedido con entregas o facturas.'))
        return super().write(vals)

    def action_confirm(self):
        self._check_sale_channel_configuration()
        for order in self:
            if not order.sale_channel_id.active:
                raise UserError(_('No se puede confirmar un pedido con un canal archivado.'))
        return super().action_confirm()

    def _prepare_invoice(self):
        self.ensure_one()
        self._check_sale_channel_configuration()
        values = super()._prepare_invoice()
        values.update({
            'sale_channel_id': self.sale_channel_id.id,
            'journal_id': self.sale_channel_id.journal_id.id,
        })
        return values

    def _get_invoice_grouping_keys(self):
        # An invoice must represent exactly one channel and its journal.
        return list(dict.fromkeys(
            super()._get_invoice_grouping_keys() + ['sale_channel_id', 'journal_id']
        ))
