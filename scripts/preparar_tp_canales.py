#!/usr/bin/env python3
"""Install/update and populate the dedicated practice database. Run on Ubuntu VM."""
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DATABASE = 'tp_canales'
MODULE = 'sale_channel_tp'
COMPOSE = ['docker', 'compose', '-f', 'devel.yaml', '-f', 'compose.tp-canales.yaml']


def command(args, *, capture=False, input_text=None):
    result = subprocess.run(
        args, cwd=ROOT, text=True, encoding='utf-8',
        input=input_text, stdout=subprocess.PIPE if capture else None,
        check=True,
    )
    return result.stdout.strip() if capture else ''


def sql(database, query):
    return command(COMPOSE + [
        'exec', '-T', 'db', 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
        '-U', 'odoo', '-d', database, '-Atc', query,
    ], capture=True)


def wait_for_database():
    # pg_isready exits immediately when ready; bounded retries avoid infinite waits.
    command(COMPOSE + [
        'exec', '-T', 'db', 'sh', '-c',
        'for n in $(seq 1 60); do pg_isready -q -U odoo -d postgres && exit 0; sleep 1; done; exit 1',
    ])


def module_operation():
    exists = sql('postgres', "SELECT datname FROM pg_database WHERE datname = 'tp_canales'")
    if not exists:
        return '-i'
    initialized = sql(DATABASE, "SELECT to_regclass('public.ir_module_module') IS NOT NULL")
    if initialized != 't':
        return '-i'
    state = sql(DATABASE, "SELECT state FROM ir_module_module WHERE name = 'sale_channel_tp'")
    return '-u' if state in ('installed', 'to upgrade') else '-i'


def main():
    for required in ('devel.yaml', 'compose.tp-canales.yaml', 'scripts/cargar_demo_tp_canales.py'):
        if not (ROOT / required).is_file():
            raise RuntimeError(f'Falta {required}. Ejecutá git pull --ff-only en ~/odoo19.')
    command(['docker', 'compose', 'version'], capture=True)
    print('1/4 - Preparando PostgreSQL...', flush=True)
    command(COMPOSE + ['up', '-d', 'db'])
    wait_for_database()
    operation = module_operation()
    print('2/4 - Instalando o actualizando sale_channel_tp en tp_canales...', flush=True)
    command(COMPOSE + ['stop', 'odoo'])
    command(COMPOSE + [
        'run', '--rm', '-T', 'odoo', 'odoo', '-d', DATABASE,
        operation, MODULE, '--without-demo=all', '--load-language=es_AR',
        '--workers=0', '--stop-after-init',
    ])
    print('3/4 - Cargando configuración y ejemplos de práctica...', flush=True)
    seed = (ROOT / 'scripts/cargar_demo_tp_canales.py').read_text(encoding='utf-8')
    command(COMPOSE + [
        'run', '--rm', '-T', 'odoo', 'odoo', 'shell', '-d', DATABASE,
        '--no-http', '--workers=0',
    ], input_text=seed)
    print('4/4 - Iniciando Odoo...', flush=True)
    command(COMPOSE + ['up', '-d'])
    print('\nListo. Abrí http://localhost:19069/web/login?db=tp_canales')
    print('La base de inmobiliaria devel conserva sus datos.')


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, OSError, RuntimeError) as error:
        print(f'\nLa preparación se detuvo: {error}', file=sys.stderr)
        print('Conservá el error anterior. Podés repetir este comando después de corregirlo.', file=sys.stderr)
        sys.exit(1)
