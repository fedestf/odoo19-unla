from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, new_test_user, tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestSaleChannel(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({'name': 'TP principal', 'code': 'TPP'})
        cls.warehouse_b = cls.env['stock.warehouse'].create({'name': 'TP secundario', 'code': 'TPS'})
        cls.journal = cls.company_data['default_journal_sale']
        cls.journal_b = cls.journal.copy({'name': 'Ventas TP B', 'code': 'TPB'})
        cls.channel = cls.env['sale.channel.tp'].create({
            'name': 'Presencial', 'code': 'TP-PRES',
            'warehouse_id': cls.warehouse.id, 'journal_id': cls.journal.id,
        })
        cls.channel_b = cls.env['sale.channel.tp'].create({
            'name': 'Web', 'code': 'TP-WEB',
            'warehouse_id': cls.warehouse_b.id, 'journal_id': cls.journal_b.id,
        })
        cls.product_a.write({'type': 'consu', 'invoice_policy': 'order', 'sale_ok': True})

    def make_order(self, channel=None):
        return self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'sale_channel_id': (channel or self.channel).id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 2, 'price_unit': 100,
            })],
        })

    def test_normalization_and_unique_code(self):
        self.assertEqual(self.channel.code, 'TP-PRES')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.channel_b.code = ' tp-pres '

    def test_blank_code(self):
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.channel_b.code = '   '

    def test_wrong_journal_type(self):
        journal = self.journal.copy({'type': 'general', 'name': 'General TP', 'code': 'TPG'})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.channel_b.journal_id = journal

    def test_other_company_warehouse(self):
        company = self.env['res.company'].create({'name': 'Otra compañía TP'})
        warehouse = self.env['stock.warehouse'].create({
            'name': 'Otro depósito TP', 'code': 'TPO', 'company_id': company.id,
        })
        with self.assertRaises(UserError), self.cr.savepoint():
            self.channel_b.warehouse_id = warehouse

    def test_channel_required(self):
        with self.assertRaises((ValidationError, UserError, IntegrityError)), self.cr.savepoint():
            self.env['sale.order'].create({'partner_id': self.partner_a.id})

    def test_compute_and_change_channel(self):
        order = self.make_order()
        self.assertEqual(order.warehouse_id, self.warehouse)
        self.assertEqual(order.journal_id, self.journal)
        order.sale_channel_id = self.channel_b
        self.assertEqual(order.warehouse_id, self.warehouse_b)
        self.assertEqual(order.journal_id, self.journal_b)

    def test_form_changes_warehouse(self):
        with Form(self.env['sale.order']) as form:
            form.partner_id = self.partner_a
            form.sale_channel_id = self.channel
            self.assertEqual(form.warehouse_id, self.warehouse)
            form.sale_channel_id = self.channel_b
            self.assertEqual(form.warehouse_id, self.warehouse_b)

    def test_explicit_wrong_warehouse_rejected(self):
        order = self.make_order()
        with self.assertRaises(ValidationError), self.cr.savepoint():
            order.warehouse_id = self.warehouse_b

    def test_configuration_cannot_change_after_use(self):
        self.make_order()
        with self.assertRaises(UserError), self.cr.savepoint():
            self.channel.journal_id = self.journal_b

    def test_confirm_creates_delivery_with_channel_and_warehouse(self):
        order = self.make_order(self.channel_b)
        order.action_confirm()
        self.assertTrue(order.picking_ids)
        for picking in order.picking_ids:
            self.assertEqual(picking.sale_channel_id, self.channel_b)
            self.assertEqual(picking.picking_type_id.warehouse_id, self.warehouse_b)

    def test_channel_locked_after_confirmation(self):
        order = self.make_order()
        order.action_confirm()
        with self.assertRaises(UserError), self.cr.savepoint():
            order.sale_channel_id = self.channel_b

    def test_archived_channel_cannot_confirm(self):
        order = self.make_order()
        self.channel.active = False
        with self.assertRaises(UserError), self.cr.savepoint():
            order.action_confirm()

    def test_invoice_channel_and_journal(self):
        order = self.make_order(self.channel_b)
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertEqual(invoice.sale_channel_id, self.channel_b)
        self.assertEqual(invoice.journal_id, self.journal_b)
        self.assertEqual(invoice.state, 'draft')
        with self.assertRaises(ValidationError), self.cr.savepoint():
            invoice.journal_id = self.journal

    def test_batch_invoicing_separates_channels(self):
        # Even the same journal must not merge channels.
        self.channel_b.journal_id = self.journal
        orders = self.make_order() | self.make_order(self.channel_b)
        orders.action_confirm()
        invoices = orders._create_invoices(grouped=False)
        self.assertEqual(len(invoices), 2)
        self.assertEqual(set(invoices.sale_channel_id.ids), {self.channel.id, self.channel_b.id})

    def test_same_channel_can_group(self):
        orders = self.make_order() | self.make_order()
        orders.action_confirm()
        invoices = orders._create_invoices(grouped=False)
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices.sale_channel_id, self.channel)

    def test_salesperson_can_read_but_not_configure(self):
        user = new_test_user(self.env, login='tp_salesperson', groups='sales_team.group_sale_salesman')
        self.assertEqual(self.channel.with_user(user).name, 'Presencial')
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.channel.with_user(user).write({'name': 'No autorizado'})

    def test_grouping_on_all_documents(self):
        order = self.make_order()
        order.action_confirm()
        invoice = order._create_invoices()
        for model, records in (
            ('sale.order', order), ('stock.picking', order.picking_ids), ('account.move', invoice),
        ):
            groups = self.env[model]._read_group(
                [('id', 'in', records.ids)], ['sale_channel_id'], ['__count'],
            )
            self.assertEqual(groups[0][0], self.channel)
