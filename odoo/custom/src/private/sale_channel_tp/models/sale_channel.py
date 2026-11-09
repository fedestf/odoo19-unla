from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleChannel(models.Model):
    _name = 'sale.channel.tp'
    _description = 'Canal de venta'
    _order = 'name, id'
    _check_company_auto = True

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True, index=True, copy=False)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Depósito', required=True,
        check_company=True, ondelete='restrict',
        domain="[('company_id', '=', company_id)]",
    )
    journal_id = fields.Many2one(
        'account.journal', string='Diario de facturación', required=True,
        check_company=True, ondelete='restrict',
        domain="[('type', '=', 'sale'), ('company_id', '=', company_id)]",
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)', 'El código del canal no puede repetirse en el sistema.',
    )

    @staticmethod
    def _normalize_code(value):
        return value.strip().upper() if isinstance(value, str) else value

    @api.model_create_multi
    def create(self, vals_list):
        values = [dict(vals) for vals in vals_list]
        for vals in values:
            if 'code' in vals:
                vals['code'] = self._normalize_code(vals['code'])
        return super().create(values)

    def write(self, vals):
        vals = dict(vals)
        if 'code' in vals:
            vals['code'] = self._normalize_code(vals['code'])
        if {'warehouse_id', 'journal_id', 'company_id'} & vals.keys():
            for channel in self:
                changed = any(
                    key in vals and vals[key] != channel[key].id
                    for key in ('warehouse_id', 'journal_id', 'company_id')
                )
                # Only an existence check: also protects orders hidden by sales rules.
                if changed and self.env['sale.order'].sudo().search_count(
                    [('sale_channel_id', '=', channel.id)], limit=1,
                ):
                    raise UserError(_(
                        'No se puede cambiar el depósito, diario o compañía de un '
                        'canal utilizado en pedidos. Cree otro canal para la nueva configuración.'
                    ))
        return super().write(vals)

    @api.constrains('name', 'code', 'journal_id', 'warehouse_id', 'company_id')
    def _check_configuration(self):
        for channel in self:
            if not (channel.name or '').strip() or not (channel.code or '').strip():
                raise ValidationError(_('El nombre y el código no pueden estar vacíos.'))
            if channel.journal_id.type != 'sale':
                raise ValidationError(_('El diario del canal debe ser de ventas.'))
            if (channel.warehouse_id.company_id != channel.company_id
                    or channel.journal_id.company_id != channel.company_id):
                raise ValidationError(_('El depósito y el diario deben pertenecer a la compañía del canal.'))
