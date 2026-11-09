"""Checks for the launcher and idempotent fixture loader; no Docker/Odoo required."""
import ast
from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import subprocess
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prepare', ROOT / 'scripts/preparar_tp_canales.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def seed_function(name):
    tree = ast.parse((ROOT / 'scripts/cargar_demo_tp_canales.py').read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    code = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    scope = {'DATABASE': 'tp_canales', 'NAMESPACE': 'tp_canales_fixture'}
    exec(compile(code, 'seed', 'exec'), scope)
    return scope[name]


class Record:
    def __init__(self, model='res.partner', **values):
        self._name = model
        self.id = 7
        self.__dict__.update(values)

    def exists(self):
        return self

    def __getitem__(self, name):
        return getattr(self, name)


class Empty:
    def __bool__(self):
        return False


class Metadata:
    model = 'res.partner'
    res_id = 7

    def __init__(self, existing=True):
        self.existing = existing
        self.created = []

    def __bool__(self):
        return self.existing

    def search(self, domain, limit=None):
        return self

    def create(self, values):
        self.created.append(values)

    def write(self, values):
        self.__dict__.update(values)


class Model:
    def __init__(self, candidates=None):
        self.candidates = candidates or []
        self.created = []

    def __bool__(self):
        return False

    def with_context(self, **kwargs):
        return self

    def search(self, domain, limit=None):
        return self.candidates

    def create(self, values):
        self.created.append(values)
        return Record(**values)


class Env:
    def __init__(self, record=None):
        self.record = record
        self.metadata = Metadata(existing=bool(record))
        self.model = Model()

    def ref(self, name, **kwargs):
        return self.record

    def __getitem__(self, name):
        return self.metadata if name == 'ir.model.data' else self.model


class SetupTests(unittest.TestCase):
    def test_missing_database_installs(self):
        with patch.object(prepare, 'sql', return_value='') as sql:
            self.assertEqual(prepare.module_operation(), '-i')
            self.assertEqual(sql.call_count, 1)

    def test_empty_database_installs(self):
        with patch.object(prepare, 'sql', side_effect=['tp_canales', 'f']):
            self.assertEqual(prepare.module_operation(), '-i')

    def test_existing_installation_updates(self):
        with patch.object(prepare, 'sql', side_effect=['tp_canales', 't', 'installed']):
            self.assertEqual(prepare.module_operation(), '-u')

    def test_uninstalled_module_installs(self):
        with patch.object(prepare, 'sql', side_effect=['tp_canales', 't', 'uninstalled']):
            self.assertEqual(prepare.module_operation(), '-i')

    def test_launcher_uses_only_dedicated_database(self):
        with patch.object(Path, 'is_file', return_value=True), patch.object(prepare, 'command') as command, patch.object(prepare, 'module_operation', return_value='-i'), redirect_stdout(io.StringIO()):
            prepare.main()
        calls = command.call_args_list
        init = next(c.args[0] for c in calls if '--stop-after-init' in c.args[0])
        self.assertEqual(init[init.index('-d') + 1], 'tp_canales')
        self.assertIn('sale_channel_tp', init)
        shell = next(c for c in calls if 'shell' in c.args[0])
        self.assertEqual(shell.args[0][shell.args[0].index('-d') + 1], 'tp_canales')
        self.assertIn('input_text', shell.kwargs)
        all_args = repr([c.args[0] for c in calls])
        for forbidden in ('resetdb', 'dropdb', '--volumes'):
            self.assertNotIn(forbidden, all_args)

    def test_launcher_stops_after_failed_install(self):
        def fail(args, **kwargs):
            if '--stop-after-init' in args:
                raise subprocess.CalledProcessError(1, args)
        with patch.object(Path, 'is_file', return_value=True), patch.object(prepare, 'command', side_effect=fail) as command, patch.object(prepare, 'module_operation', return_value='-i'), redirect_stdout(io.StringIO()):
            with self.assertRaises(subprocess.CalledProcessError):
                prepare.main()
        self.assertFalse(any('shell' in c.args[0] for c in command.call_args_list))

    def test_seed_rejects_other_databases_before_any_write(self):
        load = seed_function('load_demo')
        for name in ('devel', 'postgres', 'tp_canales_test'):
            with self.subTest(database=name), self.assertRaises(RuntimeError):
                load(NS(cr=NS(dbname=name)))

    def test_fixture_reuses_owned_record(self):
        record = Record(name='Cliente')
        env = Env(record)
        result = seed_function('ensure_record')(env, 'customer', 'res.partner', {'name': 'Nuevo'})
        self.assertIs(result, record)
        self.assertEqual(env.model.created, [])
        self.assertEqual(record.name, 'Cliente')

    def test_fixture_creates_once_and_registers_id(self):
        env = Env()
        result = seed_function('ensure_record')(env, 'customer', 'res.partner', {'name': 'Cliente'})
        self.assertEqual(result.name, 'Cliente')
        self.assertEqual(len(env.model.created), 1)
        self.assertEqual(env.metadata.created[0]['module'], 'tp_canales_fixture')

    def test_fixture_rejects_modified_configuration_without_overwrite(self):
        record = Record(name='Cliente', active=False)
        env = Env(record)
        with self.assertRaises(RuntimeError):
            seed_function('ensure_record')(env, 'customer', 'res.partner', {}, expected={'active': True})
        self.assertFalse(record.active)
        self.assertEqual(env.model.created, [])

    def test_fixture_rejects_wrong_model(self):
        with self.assertRaises(RuntimeError):
            seed_function('ensure_record')(Env(Record(model='res.users')), 'customer', 'res.partner', {})

    def test_seed_scripts_parse(self):
        for path in (ROOT / 'scripts').glob('*.py'):
            compile(path.read_text(encoding='utf-8'), str(path), 'exec')


if __name__ == '__main__':
    unittest.main()
