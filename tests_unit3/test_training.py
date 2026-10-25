"""Pruebas con Pytest, sin servidor Odoo. Los casos ORM están en el addon."""
import ast
import csv
import gettext
import io
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po
from lxml import etree
from markupsafe import Markup
import pytest


ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'odoo/custom/src/private/real_estate_training'


class UserError(Exception):
    pass


class AccessError(Exception):
    pass


def method(path, name):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    node.decorator_list = []
    namespace = {'_': lambda text: text, 'UserError': UserError, 'AccessError': AccessError, 'Markup': Markup}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


class Properties(list):
    def __init__(self, states):
        super().__init__(SimpleNamespace(state=state, salesman_id=1) for state in states)
        self.access_checked = False

    def exists(self):
        return self

    def check_access(self, operation):
        assert operation == 'write'
        self.access_checked = True

    def write(self, values):
        assert self.access_checked
        for record in self:
            record.salesman_id = values['salesman_id']


def wizard(states, manager=True, active=True, share=False):
    return SimpleNamespace(
        env=SimpleNamespace(su=False, user=SimpleNamespace(has_group=lambda group: manager)),
        ensure_one=lambda: None, property_ids=Properties(states),
        salesman_id=SimpleNamespace(id=42, active=active, share=share),
    )


APPLY = method(ADDON / 'wizard/assign_salesman.py', 'action_apply')


def test_wizard_updates_all_selected_properties():
    record = wizard(['new', 'offer_received'])
    assert APPLY(record)['type'] == 'ir.actions.act_window_close'
    assert [p.salesman_id for p in record.property_ids] == [42, 42]


@pytest.mark.parametrize('state', ['sold', 'canceled'])
def test_wizard_blocks_whole_batch_before_write(state):
    record = wizard(['new', state])
    with pytest.raises(UserError):
        APPLY(record)
    assert [p.salesman_id for p in record.property_ids] == [1, 1]


def test_wizard_rejects_non_manager():
    with pytest.raises(AccessError):
        APPLY(wizard(['new'], manager=False))


def test_wizard_requires_property():
    with pytest.raises(UserError):
        APPLY(wizard([]))


@pytest.mark.parametrize('active,share', [(False, False), (True, True)])
def test_wizard_rejects_inactive_or_portal_user(active, share):
    with pytest.raises(UserError):
        APPLY(wizard(['new'], active=active, share=share))


class Server(SimpleNamespace):
    def sudo(self):
        return self


class MailEnv:
    def __init__(self):
        self.server = Server(id=3, active=True, smtp_host='smtp', smtp_port=1025,
                             smtp_authentication='login', smtp_encryption='none', smtp_user=False, smtp_pass=False)
        self.payload = None
        self.sent = False

    def ref(self, xmlid):
        assert xmlid == 'real_estate_training.mailhog_training_server'
        return self.server

    def __getitem__(self, name):
        assert name == 'mail.mail'
        return self

    def sudo(self):
        return self

    def create(self, values):
        self.payload = values
        return self

    def send(self, raise_exception):
        assert raise_exception
        self.sent = True


def mail_property():
    return SimpleNamespace(
        env=MailEnv(), name='<script>bad()</script>', ensure_one=lambda: None,
        _check_training_manager=lambda: None, check_access=lambda mode: None,
    )


SEND = method(ADDON / 'models/estate_property.py', 'action_training_mailhog')


def test_mail_fixed_destination_and_html_escaping():
    record = mail_property()
    result = SEND(record)
    assert record.env.sent
    assert record.env.payload['email_to'] == 'odoo-study@localhost.test'
    assert record.env.payload['mail_server_id'] == 3
    assert '<script>' not in record.env.payload['body_html']
    assert '&lt;script&gt;' in record.env.payload['body_html']
    assert result['params']['type'] == 'success'


@pytest.mark.parametrize('field,value', [
    ('active', False), ('smtp_host', 'external.example'), ('smtp_port', 25),
    ('smtp_authentication', 'cli'), ('smtp_encryption', 'starttls'),
    ('smtp_user', 'someone'), ('smtp_pass', 'configured'),
])
def test_mail_refuses_other_routes_before_creating_mail(field, value):
    record = mail_property()
    setattr(record.env.server, field, value)
    with pytest.raises(UserError):
        SEND(record)
    assert record.env.payload is None
    assert not record.env.sent


def test_manager_check_is_server_side():
    check = method(ADDON / 'models/estate_property.py', '_check_training_manager')
    record = SimpleNamespace(env=SimpleNamespace(su=False, user=SimpleNamespace(has_group=lambda group: False)))
    with pytest.raises(AccessError):
        check(record)


@pytest.mark.parametrize('language', ['es', 'es_AR'])
def test_translations_compile_and_translate(language):
    with (ADDON / 'i18n' / f'{language}.po').open(encoding='utf-8') as source:
        catalog = read_po(source)
    assert not list(catalog.check())
    binary = io.BytesIO()
    write_mo(binary, catalog)
    binary.seek(0)
    translation = gettext.GNUTranslations(binary)
    assert translation.gettext('Assign salesperson') == 'Asignar vendedor'
    assert translation.gettext('Property sheet') == 'Ficha de propiedad'
    assert translation.gettext('Daily snapshots') == 'Resúmenes diarios'
    assert len(catalog) >= 40


def test_manifest_files_and_wizard_acl():
    manifest = ast.literal_eval((ADDON / '__manifest__.py').read_text(encoding='utf-8'))
    assert manifest['depends'] == ['real_estate', 'mail']
    for name in manifest['data']:
        assert (ADDON / name).is_file()
    with (ADDON / 'security/ir.model.access.csv').open(encoding='utf-8', newline='') as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 2
    assert all(row['group_id:id'] == 'real_estate.group_estate_property_manager' for row in rows)


def test_all_python_and_xml_parse():
    for path in ADDON.rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    for path in ADDON.rglob('*.xml'):
        etree.parse(str(path))


def test_qweb_uses_escaped_fields_and_report_action():
    root = etree.parse(str(ADDON / 'report/property_report.xml'))
    assert root.xpath('string(//record/field[@name="report_type"])') == 'qweb-pdf'
    assert root.xpath('//t[@t-foreach="docs"]')
    assert root.xpath('//tr[@t-foreach="o.offer_ids"]')
    assert not root.xpath('//*[@t-raw]')
    assert root.xpath('//*[@t-field="o.name"]')


def test_cron_daily_active_and_mailhog_configuration():
    cron = etree.parse(str(ADDON / 'data/snapshot_cron.xml'))
    assert cron.xpath('string(//field[@name="interval_type"])') == 'days'
    assert cron.xpath('string(//field[@name="code"])') == 'model._cron_capture_daily()'
    assert not cron.xpath('//field[@name="numbercall"]')
    server = etree.parse(str(ADDON / 'data/mailhog_server.xml'))
    assert server.xpath('string(//field[@name="smtp_host"])') == 'smtp'
    assert server.xpath('string(//field[@name="smtp_port"])') == '1025'


def test_snapshot_reuses_same_day_and_refreshes_counts():
    capture = method(ADDON / 'models/snapshot.py', '_capture_today')
    capture.__globals__['fields'] = SimpleNamespace(
        Date=SimpleNamespace(context_today=lambda model: date(2026, 10, 24)),
        Datetime=SimpleNamespace(now=lambda: datetime(2026, 10, 24, 12)),
    )
    class Model:
        def __init__(self):
            self.snapshot = None
            self.total = 8
            self.env = self

        def __getitem__(self, name):
            assert name in ('estate.property', 'estate.property.offer')
            return SimpleNamespace(search_count=lambda domain: 3 if domain else self.total)

        def search(self, domain, limit):
            return self.snapshot

        def create(self, values):
            self.snapshot = SimpleNamespace(**values)
            self.snapshot.write = lambda values: self.snapshot.__dict__.update(values)
            return self.snapshot

    model = Model()
    first = capture(model)
    assert first.property_count == 8
    assert first.available_count == 3
    model.total = 9
    second = capture(model)
    assert first is second
    assert second.property_count == 9
    assert second.capture_date == date(2026, 10, 24)
