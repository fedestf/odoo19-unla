"""Pruebas aisladas de métodos reales; no sustituye pruebas ORM/PostgreSQL."""
import ast
import math
import random
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1] / 'odoo/custom/src/private'


class UserError(Exception):
    pass


class Command:
    clear = staticmethod(lambda: (5, 0, 0))
    set = staticmethod(lambda ids: (6, 0, ids))
    link = staticmethod(lambda id: (4, id, 0))
    create = staticmethod(lambda values: (0, 0, values))


class Records(list):
    def __init__(self, values=(), env=None):
        super().__init__(values)
        self.env = env

    @property
    def ids(self):
        return [r.id for r in self]

    def ensure_one(self):
        assert len(self) == 1

    def __getattr__(self, name):
        self.ensure_one()
        return getattr(self[0], name)

    def __or__(self, other):
        return Records(list({r.id: r for r in [*self, *other]}.values()), self.env)

    def __ior__(self, other):
        return self | other

    def __sub__(self, other):
        return Records([r for r in self if r not in other], self.env)

    def exists(self):
        return self

    def check_access(self, operation):
        assert operation == 'write'

    def write(self, values):
        for record in self:
            for key, value in values.items():
                setattr(record, key, value)
        return True

    def mapped(self, name):
        values = [getattr(r, name) for r in self]
        return values


class Property(SimpleNamespace):
    @property
    def offer_ids(self):
        return Records([r for r in self.env.offers if r.property_id.id == self.id], self.env)

    @property
    def best_offer(self):
        return max(self.offer_ids.mapped('price'), default=0)

    @property
    def offer_partner_ids(self):
        return Records(list({r.partner_id.id: r.partner_id for r in self.offer_ids}.values()))

    def write(self, values):
        for key, value in values.items():
            setattr(self, key, value)
        return True


class PropertyModel:
    def __init__(self, env):
        self.env = env

    def browse(self, id):
        return Records([self.env.property] if id == self.env.property.id else [], self.env)

    def __or__(self, other):
        return other


class BaseOffer:
    def default_get(self, fields):
        return {}

    def create(self, values_list):
        result = []
        for values in values_list:
            record = SimpleNamespace(
                id=len(self.env.offers) + 1,
                property_id=self.env.property,
                partner_id=SimpleNamespace(id=values['partner_id']),
                price=values['price'], status=False,
            )
            self.env.offers.append(record)
            result.append(record)
        return Records(result, self.env)


def build_class(path, name, method_names, base=object):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in method_names]
    for method in methods:
        method.decorator_list = []
    new_class = ast.ClassDef(name=name, bases=[ast.Name(id='Base', ctx=ast.Load())], keywords=[], body=methods, decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[new_class], type_ignores=[]))
    ns = {'Base': base, 'UserError': UserError, '_': lambda text, **kw: text % kw if kw else text, 'math': math, 'random': random, 'Command': Command}
    exec(compile(module, str(path), 'exec'), ns)
    return ns[name]


OfferMethods = build_class(ROOT / 'real_estate/models/estate_property_offer.py', 'Offer', ['create', 'action_accept'], BaseOffer)


class Offer(OfferMethods):
    def create(self, values):
        # Emula solo la normalización dict->lista de @api.model_create_multi.
        return super().create([values] if isinstance(values, dict) else values)
Actions = build_class(ROOT / 'real_estate/models/estate_property.py', 'Actions', ['action_generate_offer', '_unlink_if_new_or_cancelled', 'action_clear_tags', 'action_load_all_tags', 'action_add_brand_new_tag'], Records)


class Env:
    def __init__(self):
        self.offers = []
        self.property = Property(id=1, name='Prueba', state='new', expected_price=100000, env=self)
        self.offer_model = Offer()
        self.offer_model.env = self
        self.company = SimpleNamespace(id=1, ids=[1])
        self.created_invoices = []

    def __getitem__(self, model):
        if model == 'estate.property':
            return PropertyModel(self)
        if model == 'estate.property.offer':
            return self.offer_model
        if model == 'res.partner':
            return SimpleNamespace(search=lambda domain: Records([SimpleNamespace(id=id, active=True) for id in (1, 2, 3) if id not in self.property.offer_partner_ids.ids]))
        if model == 'account.journal':
            return SimpleNamespace(search=lambda domain, limit: SimpleNamespace(id=1, default_account_id=SimpleNamespace(id=9)))
        if model == 'account.move':
            return self
        raise AssertionError(model)

    def with_context(self, **kwargs):
        return self

    def create(self, values):
        invoice = SimpleNamespace(id=len(self.created_invoices) + 1, **values)
        self.created_invoices.append(invoice)
        return invoice


class BaseSale(Records):
    def filtered(self, predicate):
        return type(self)([r for r in self if predicate(r)], self.env)

    def action_sold(self):
        for record in self:
            if record.state == 'canceled':
                raise UserError('cancelada')
        self.write({'state': 'sold'})
        return True


Sale = build_class(ROOT / 'estate_account/models/estate_property.py', 'Sale', ['action_sold'], BaseSale)


class Unit2Tests(unittest.TestCase):
    def setUp(self):
        self.env = Env()

    def create_offer(self, price, partner=1):
        return self.env.offer_model.create([{'price': price, 'property_id': 1, 'partner_id': partner}])

    def test_offer_increases_and_changes_state(self):
        self.create_offer(50000)
        self.create_offer(65000, 2)
        self.assertEqual(self.env.property.state, 'offer_received')
        self.assertEqual(self.env.property.best_offer, 65000)

    def test_lower_and_equal_blocked(self):
        self.create_offer(50000)
        for price in (49000, 50000):
            with self.assertRaises(UserError):
                self.create_offer(price, 2)
        self.assertEqual(len(self.env.offers), 1)

    def test_closed_states(self):
        for state in ('sold', 'canceled', 'offer_accepted'):
            self.env.property.state = state
            with self.assertRaises(UserError):
                self.create_offer(100000)

    def test_batch_order(self):
        with self.assertRaises(UserError):
            self.env.offer_model.create([{'price': 50000, 'property_id': 1, 'partner_id': 1}, {'price': 49000, 'property_id': 1, 'partner_id': 2}])
        self.assertFalse(self.env.offers)

    def test_accept_sets_buyer_and_rejects_others(self):
        first = self.create_offer(50000)
        second = self.create_offer(65000, 2)
        self.env.offer_model.action_accept.__func__(second)
        self.assertEqual(first.status, 'refused')
        self.assertEqual(second.status, 'accepted')
        self.assertEqual(self.env.property.buyer_id, 2)
        self.assertEqual(self.env.property.selling_price, 65000)
        self.assertEqual(self.env.property.state, 'offer_accepted')

    def test_automatic_range_and_unique_contacts(self):
        records = Actions([self.env.property], self.env)
        records.action_generate_offer()
        first = self.env.offers[0]
        self.assertTrue(70000 <= first.price <= 130000)
        if first.price < 130000:
            records.action_generate_offer()
            self.assertNotEqual(first.partner_id.id, self.env.offers[1].partner_id.id)
            self.assertGreater(self.env.offers[1].price, first.price)

    def test_automatic_impossible_range(self):
        self.create_offer(130000)
        with self.assertRaises(UserError):
            Actions([self.env.property], self.env).action_generate_offer()

    def test_delete_allowed_and_blocked_states(self):
        records = Actions([self.env.property], self.env)
        for state in ('new', 'canceled'):
            self.env.property.state = state
            records._unlink_if_new_or_cancelled()
        for state in ('sold', 'offer_received', 'offer_accepted'):
            self.env.property.state = state
            with self.assertRaises(UserError):
                records._unlink_if_new_or_cancelled()

    def test_invoice_payload_and_idempotence(self):
        prop = self.env.property
        prop.buyer_id = SimpleNamespace(id=42)
        prop.selling_price = 100000
        prop.invoice_id = False
        sale = Sale([prop], self.env)
        sale.action_sold()
        invoice = prop.invoice_id
        self.assertEqual(invoice.partner_id, 42)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual([c[2]['price_unit'] for c in invoice.invoice_line_ids], [100000, 100])
        self.assertEqual([c[2]['quantity'] for c in invoice.invoice_line_ids], [1, 1])
        self.assertEqual(invoice.invoice_line_ids[1][2]['name'], 'Gastos administrativos')
        sale.action_sold()
        self.assertEqual(len(self.env.created_invoices), 1)

    def test_invoice_missing_buyer(self):
        prop = self.env.property
        prop.buyer_id = False
        prop.selling_price = 100000
        prop.invoice_id = False
        with self.assertRaises(UserError):
            Sale([prop], self.env).action_sold()
        self.assertEqual(prop.state, 'new')
        self.assertFalse(self.env.created_invoices)


if __name__ == '__main__':
    unittest.main(verbosity=2)

