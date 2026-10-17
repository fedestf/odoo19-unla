from odoo import Command, _, fields, models
from odoo.exceptions import UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Factura de venta",
        readonly=True,
        copy=False,
        groups="account.group_account_invoice",
        ondelete="restrict",
    )

    def action_sold(self):
        to_invoice = self.filtered(lambda record: record.state != "sold")
        for property_record in to_invoice:
            if not property_record.buyer_id:
                raise UserError(_("Seleccioná un comprador antes de facturar la venta."))
            if property_record.selling_price <= 0:
                raise UserError(_("El precio de venta debe ser positivo para generar la factura."))
        result = super().action_sold()
        if not to_invoice:
            return result
        journal = self.env["account.journal"].search([
            ("type", "=", "sale"),
            ("company_id", "=", self.env.company.id),
        ], limit=1)
        if not journal:
            raise UserError(_("Configurá un diario de ventas en la compañía actual antes de facturar."))
        income_account = journal.default_account_id
        if not income_account:
            income_account = self.env["account.account"].search([
                ("company_ids", "in", self.env.company.ids),
                ("account_type", "in", ["income", "income_other"]),
            ], limit=1)
        if not income_account:
            raise UserError(_("Configurá una cuenta de ingresos para la compañía actual."))
        for property_record in to_invoice:
            if property_record.invoice_id:
                raise UserError(_("Esta propiedad ya tiene una factura de venta vinculada."))
            invoice = self.env["account.move"].with_context(default_move_type="out_invoice").create({
                "move_type": "out_invoice",
                "partner_id": property_record.buyer_id.id,
                "company_id": self.env.company.id,
                "journal_id": journal.id,
                "invoice_origin": property_record.name,
                "invoice_line_ids": [
                    Command.create({
                        "name": property_record.name,
                        "quantity": 1,
                        "price_unit": property_record.selling_price,
                        "account_id": income_account.id,
                    }),
                    Command.create({
                        "name": "Gastos administrativos",
                        "quantity": 1,
                        "price_unit": 100,
                        "account_id": income_account.id,
                    }),
                ],
            })
            property_record.invoice_id = invoice
        return result
