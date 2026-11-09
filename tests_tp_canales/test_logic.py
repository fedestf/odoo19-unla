"""Checks without an Odoo server. Run: python -m unittest discover -s tests_tp_canales -v."""
import ast
import csv
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'odoo/custom/src/private/sale_channel_tp'


class ValidationError(Exception):
    pass


class UserError(Exception):
    pass


class Base:
    def _compute_warehouse_id(self):
        for order in self:
            order.warehouse_id = None

    def _compute_journal_id(self):
        for order in self:
            order.journal_id = None

    def _get_invoice_grouping_keys(self):
        return ['company_id', 'partner_id', 'currency_id', 'journal_id']

    def _prepare_invoice(self):
        return {'partner_id': 55, 'journal_id': 999}

    def action_confirm(self):
        self.confirmed = True
        return True

    def write(self, vals):
        self.written = vals
        return True


def methods(filename, names, base=Base):
    tree = ast.parse((ADDON / 'models' / filename).read_text(encoding='utf-8'))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    body = []
    for node in original.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            node.decorator_list = [
                d for d in node.decorator_list if isinstance(d, ast.Name) and d.id == 'staticmethod'
            ]
            body.append(node)
    cls = ast.ClassDef(name='ActualMethods', bases=[ast.Name(id='Base', ctx=ast.Load())], keywords=[], body=body, decorator_list=[])
    mod = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    scope = {'Base': base, '_': lambda s: s, 'ValidationError': ValidationError, 'UserError': UserError}
    exec(compile(mod, filename, 'exec'), scope)
    return scope['ActualMethods']


class Records(list):
    def ensure_one(self):
        assert len(self) == 1

    def __getattr__(self, name):
        self.ensure_one()
        return getattr(self[0], name)


def order_record():
    company = NS(id=1)
    wh, journal = NS(id=10), NS(id=20)
    channel = NS(id=30, company_id=company, warehouse_id=wh, journal_id=journal, active=True)
    return NS(company_id=company, warehouse_id=wh, journal_id=journal,
              sale_channel_id=channel, state='draft', picking_ids=[], invoice_ids=[])


Order = methods('sale_order.py', {
    '_compute_warehouse_id', '_compute_journal_id', '_check_sale_channel_configuration',
    'write', 'action_confirm', '_prepare_invoice', '_get_invoice_grouping_keys',
}, type('RecordBase', (Records, Base), {}))
Channel = methods('sale_channel.py', {'_normalize_code', '_check_configuration', 'write'}, type('RecordBase', (Records, Base), {}))
Move = methods('account_move.py', {'_check_sale_channel_journal'}, Records)


class LogicTests(unittest.TestCase):
    def test_code_normalizes(self):
        self.assertEqual(Channel._normalize_code('  Web-01  '), 'WEB-01')
        self.assertIs(Channel._normalize_code(False), False)

    def test_unique_code_is_global(self):
        tree = ast.parse((ADDON / 'models/sale_channel.py').read_text(encoding='utf-8'))
        values = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)]
        self.assertIn('UNIQUE(code)', values)

    def test_required_configuration(self):
        company = NS(id=1)
        channel = NS(name='Web', code='WEB', company_id=company,
                     warehouse_id=NS(company_id=company), journal_id=NS(type='sale', company_id=company))
        Channel([channel])._check_configuration()
        for field in ('name', 'code'):
            with self.subTest(field=field):
                original = getattr(channel, field)
                setattr(channel, field, '   ')
                with self.assertRaises(ValidationError):
                    Channel([channel])._check_configuration()
                setattr(channel, field, original)

    def test_journal_type_checked_on_server(self):
        company = NS(id=1)
        channel = NS(name='Web', code='WEB', company_id=company,
                     warehouse_id=NS(company_id=company), journal_id=NS(type='purchase', company_id=company))
        with self.assertRaises(ValidationError):
            Channel([channel])._check_configuration()

    def test_channel_company_checked(self):
        channel = NS(name='Web', code='WEB', company_id=1,
                     warehouse_id=NS(company_id=2), journal_id=NS(type='sale', company_id=1))
        with self.assertRaises(ValidationError):
            Channel([channel])._check_configuration()

    def test_computes_apply_each_channel(self):
        records = Order([order_record(), order_record()])
        records[1].sale_channel_id.warehouse_id = NS(id=11)
        records[1].sale_channel_id.journal_id = NS(id=21)
        records._compute_warehouse_id()
        records._compute_journal_id()
        self.assertEqual([o.warehouse_id.id for o in records], [10, 11])
        self.assertEqual([o.journal_id.id for o in records], [20, 21])

    def test_order_configuration_valid(self):
        Order([order_record()])._check_sale_channel_configuration()

    def test_order_configuration_rejects_mismatch(self):
        for field in ('company_id', 'warehouse_id', 'journal_id', 'sale_channel_id'):
            with self.subTest(field=field):
                order = order_record()
                setattr(order, field, False)
                with self.assertRaises(ValidationError):
                    Order([order])._check_sale_channel_configuration()

    def test_channel_locked_after_confirm(self):
        for state in ('sale', 'cancel'):
            order = order_record()
            order.state = state
            records = Order([order])
            with self.assertRaises(UserError):
                records.write({'sale_channel_id': 99})
            self.assertNotIn('written', records.__dict__)

    def test_channel_locked_with_existing_documents(self):
        for field in ('picking_ids', 'invoice_ids'):
            order = order_record()
            setattr(order, field, [1])
            with self.assertRaises(UserError):
                Order([order]).write({'sale_channel_id': 99})

    def test_draft_channel_change_allowed(self):
        records = Order([order_record()])
        self.assertTrue(records.write({'sale_channel_id': 99}))
        self.assertEqual(records.written['sale_channel_id'], 99)

    def test_confirm_active_channel(self):
        records = Order([order_record()])
        self.assertTrue(records.action_confirm())
        self.assertTrue(records.confirmed)

    def test_confirm_archived_channel_rejected(self):
        order = order_record()
        order.sale_channel_id.active = False
        records = Order([order])
        with self.assertRaises(UserError):
            records.action_confirm()
        self.assertNotIn('confirmed', records.__dict__)

    def test_invoice_uses_channel_journal_and_preserves_base(self):
        values = Order([order_record()])._prepare_invoice()
        self.assertEqual(values, {'partner_id': 55, 'journal_id': 20, 'sale_channel_id': 30})

    def test_invoice_grouping_keys_preserved_and_extended(self):
        keys = Order([])._get_invoice_grouping_keys()
        self.assertEqual(keys, ['company_id', 'partner_id', 'currency_id', 'journal_id', 'sale_channel_id'])

    def test_invoice_configuration_valid_and_manual_allowed(self):
        order = order_record()
        Move([NS(sale_channel_id=order.sale_channel_id, company_id=order.company_id,
                 journal_id=order.journal_id, move_type='out_invoice')])._check_sale_channel_journal()
        Move([NS(sale_channel_id=False)])._check_sale_channel_journal()

    def test_invoice_rejects_wrong_journal_company_type(self):
        for field, value in [('journal_id', False), ('company_id', False), ('move_type', 'in_invoice')]:
            order = order_record()
            move = NS(sale_channel_id=order.sale_channel_id, company_id=order.company_id,
                      journal_id=order.journal_id, move_type='out_invoice')
            setattr(move, field, value)
            with self.assertRaises(ValidationError):
                Move([move])._check_sale_channel_journal()

    def test_all_python_and_xml_parse(self):
        for path in ADDON.rglob('*.py'):
            compile(path.read_text(encoding='utf-8'), str(path), 'exec')
        for path in ADDON.rglob('*.xml'):
            ET.parse(path)

    def test_manifest_files_exist(self):
        manifest = ast.literal_eval((ADDON / '__manifest__.py').read_text(encoding='utf-8'))
        self.assertEqual(set(manifest['depends']), {'sale_management', 'sale_stock'})
        for name in manifest['data']:
            self.assertTrue((ADDON / name).is_file(), name)

    def test_access_and_multicompany_rule(self):
        with (ADDON / 'security/ir.model.access.csv').open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            rights = [row[key] for key in ('perm_read', 'perm_write', 'perm_create', 'perm_unlink')]
            self.assertEqual(rights, ['1'] * 4 if row['group_id:id'].endswith('group_sale_manager') else ['1','0','0','0'])
        rule = ET.parse(ADDON / 'security/sale_channel_security.xml')
        self.assertEqual(rule.find('.//field[@name="domain_force"]').text, "[('company_id', 'in', company_ids)]")

    def test_all_document_searches_support_channel_grouping(self):
        for name in ('sale_order_views.xml', 'stock_picking_views.xml', 'account_move_views.xml'):
            doc = ET.parse(ADDON / 'views' / name)
            filters = doc.findall('.//filter[@name="group_by_sale_channel_tp"]')
            self.assertEqual(len(filters), 1)
            self.assertEqual(ast.literal_eval(filters[0].get('context')), {'group_by': 'sale_channel_id'})


if __name__ == '__main__':
    unittest.main()
