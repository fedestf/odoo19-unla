from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSaleInvoice(AccountTestInvoicingCommon):
    def test_invoice_lines_and_repeat_sale(self):
        property_record = self.env["estate.property"].sudo().create({
            "name": "U2 Venta facturada",
            "buyer_id": self.partner_a.id,
            "selling_price": 100000,
        })
        property_record.action_sold()
        invoice = property_record.invoice_id
        self.assertTrue(invoice)
        self.assertEqual(property_record.state, "sold")
        self.assertEqual(invoice.state, "draft")
        self.assertEqual(invoice.partner_id, self.partner_a)
        self.assertEqual(invoice.move_type, "out_invoice")
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertEqual(invoice.invoice_line_ids.mapped("quantity"), [1.0, 1.0])
        self.assertEqual(invoice.invoice_line_ids.mapped("price_unit"), [100000.0, 100.0])
        self.assertEqual(invoice.invoice_line_ids.mapped("name"), [property_record.name, "Gastos administrativos"])
        property_record.action_sold()
        self.assertEqual(property_record.invoice_id, invoice)
        self.assertFalse(property_record.copy().invoice_id)

    def test_missing_buyer_and_cancelled_sale(self):
        property_record = self.env["estate.property"].sudo().create({"name": "U2 Sin comprador", "selling_price": 1000})
        with self.assertRaises(UserError):
            property_record.action_sold()
        self.assertEqual(property_record.state, "new")
        property_record.write({"buyer_id": self.partner_a.id, "state": "canceled"})
        with self.assertRaises(UserError):
            property_record.action_sold()
        self.assertFalse(property_record.invoice_id)
