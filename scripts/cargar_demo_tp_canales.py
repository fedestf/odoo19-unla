"""Executed in Odoo shell by preparar_tp_canales.py, never imported by the addon."""
import secrets

from odoo import Command


DATABASE = 'tp_canales'
NAMESPACE = 'tp_canales_fixture'


def ensure_record(env, key, model, values, domain=None, expected=None):
    """Reuse owned IDs; adopt a matching natural key without overwriting user data."""
    xmlid = f'{NAMESPACE}.{key}'
    record = env.ref(xmlid, raise_if_not_found=False)
    if record and record._name != model:
        raise RuntimeError(f'{xmlid} apunta a un modelo incorrecto.')
    record = record.exists() if record else env[model]
    if not record and domain:
        candidates = env[model].with_context(active_test=False).search(domain, limit=2)
        if len(candidates) > 1:
            raise RuntimeError(f'Hay varios registros candidatos para {key}. No se modificaron.')
        record = candidates
    if record:
        for field, wanted in (expected or {}).items():
            value = record[field]
            actual = value.id if hasattr(value, '_name') else value
            if actual != wanted:
                raise RuntimeError(
                    f'El registro de práctica {key} tiene otra configuración en {field}. '
                    'Se conserva sin sobrescribir; revisalo antes de repetir.'
                )
    else:
        record = env[model].create(values)
    metadata = env['ir.model.data'].search([
        ('module', '=', NAMESPACE), ('name', '=', key),
    ], limit=1)
    if metadata:
        if metadata.model != model or metadata.res_id != record.id:
            metadata.write({'model': model, 'res_id': record.id})
    else:
        env['ir.model.data'].create({
            'module': NAMESPACE, 'name': key, 'model': model,
            'res_id': record.id, 'noupdate': True,
        })
    return record


def account_for(env, company, account_type):
    account = env['account.account'].search([
        ('company_ids', 'in', company.ids), ('account_type', '=', account_type),
    ], limit=1)
    if not account:
        raise RuntimeError(f'Falta una cuenta de tipo {account_type} en la compañía de práctica.')
    return account


def load_demo(shell_env):
    if shell_env.cr.dbname != DATABASE:
        raise RuntimeError('Esta carga solo puede ejecutarse en tp_canales, nunca en devel.')
    module = shell_env['ir.module.module'].search([
        ('name', '=', 'sale_channel_tp'), ('state', '=', 'installed'),
    ], limit=1)
    if not module:
        raise RuntimeError('Primero debe instalarse sale_channel_tp.')
    company = shell_env.ref('base.main_company')
    env = shell_env['res.company'].sudo().with_context(
        allowed_company_ids=company.ids,
        tracking_disable=True, mail_create_nosubscribe=True,
        mail_notrack=True, mail_notify_force_send=False, send_email=False,
    ).with_company(company).env
    company = env['res.company'].browse(company.id)

    if not company.chart_template:
        existing_accounts = env['account.account'].search_count([
            ('company_ids', 'in', company.ids),
        ], limit=1)
        if existing_accounts:
            raise RuntimeError(
                'La compañía tiene cuentas pero no un plan reconocido. '
                'Se conservó la configuración; debe revisarse antes de cargar el ejemplo.'
            )
        env['account.chart.template'].try_loading('generic_coa', company, install_demo=False)
        company.name = 'TP Canales - Práctica'
    income = account_for(env, company, 'income')
    receivable = account_for(env, company, 'asset_receivable')
    payable = account_for(env, company, 'liability_payable')

    warehouses, journals, channels = {}, {}, {}
    for key, label, code in [('local', 'Local TP', 'TPL'), ('web', 'Web TP', 'TPW')]:
        warehouses[key] = ensure_record(
            env, f'warehouse_{key}', 'stock.warehouse',
            {'name': f'Depósito {label}', 'code': code, 'company_id': company.id},
            [('code', '=', code), ('company_id', '=', company.id)],
            {'company_id': company.id, 'active': True},
        )
        journal_values = {
            'name': f'Ventas {label}', 'code': code, 'type': 'sale',
            'company_id': company.id, 'default_account_id': income.id,
        }
        # A practice draft does not require electronic/fiscal document setup.
        if 'l10n_latam_use_documents' in env['account.journal']._fields:
            journal_values['l10n_latam_use_documents'] = False
        journals[key] = ensure_record(
            env, f'journal_{key}', 'account.journal', journal_values,
            [('code', '=', code), ('company_id', '=', company.id)],
            {'company_id': company.id, 'type': 'sale', 'active': True},
        )
        channels[key] = ensure_record(
            env, f'channel_{key}', 'sale.channel.tp',
            {'name': label, 'code': f'TP-{key.upper()}', 'company_id': company.id,
             'warehouse_id': warehouses[key].id, 'journal_id': journals[key].id},
            [('code', '=', f'TP-{key.upper()}')],
            {'company_id': company.id, 'warehouse_id': warehouses[key].id,
             'journal_id': journals[key].id, 'active': True},
        )

    customer = ensure_record(
        env, 'customer', 'res.partner',
        {'name': 'Cliente prueba TP', 'ref': 'TP-CANALES-CLIENTE', 'customer_rank': 1,
         'company_id': company.id, 'email': False,
         'property_account_receivable_id': receivable.id,
         'property_account_payable_id': payable.id},
        [('ref', '=', 'TP-CANALES-CLIENTE'), ('company_id', '=', company.id)],
        {'company_id': company.id, 'active': True},
    )
    product = ensure_record(
        env, 'product', 'product.product',
        {'name': 'Producto prueba TP', 'default_code': 'TP-CANALES', 'type': 'consu',
         'is_storable': False, 'sale_ok': True, 'purchase_ok': False,
         'list_price': 100, 'invoice_policy': 'order', 'company_id': company.id,
         'taxes_id': [Command.clear()], 'supplier_taxes_id': [Command.clear()],
         'property_account_income_id': income.id},
        [('default_code', '=', 'TP-CANALES'), ('company_id', '=', company.id)],
        {'company_id': company.id, 'type': 'consu', 'invoice_policy': 'order', 'active': True},
    )

    groups = env['res.groups'].browse([
        env.ref(xmlid).id for xmlid in (
            'base.group_user', 'sales_team.group_sale_manager',
            'stock.group_stock_manager', 'stock.group_stock_multi_warehouses',
            'account.group_account_manager',
        )
    ])
    user = env.ref(f'{NAMESPACE}.user', raise_if_not_found=False)
    password = None
    if not user:
        if env['res.users'].with_context(active_test=False).search_count([('login', '=', 'tp_canales')]):
            raise RuntimeError('El login tp_canales ya existe sin pertenecer a esta carga. No se modificó.')
        password = secrets.token_urlsafe(12)
        user = ensure_record(env, 'user', 'res.users', {
            'name': 'Estudiante TP Canales', 'login': 'tp_canales', 'password': password,
            'email': False, 'lang': 'es_AR', 'company_id': company.id,
            'company_ids': [Command.set(company.ids)], 'group_ids': [Command.set(groups.ids)],
        })
    elif not user.active or user.company_id != company:
        raise RuntimeError('El usuario de práctica está archivado o cambió de compañía; no se modificó.')

    summary = []
    for key in ('local', 'web'):
        def order_values(reference):
            return {
                'partner_id': customer.id, 'company_id': company.id,
                'sale_channel_id': channels[key].id, 'user_id': user.id,
                'client_order_ref': reference,
                'order_line': [Command.create({
                    'product_id': product.id, 'product_uom_qty': 2, 'price_unit': 100,
                    'tax_ids': [Command.clear()],
                })],
            }
        expected = {'company_id': company.id, 'sale_channel_id': channels[key].id,
                    'partner_id': customer.id}
        quotation = ensure_record(env, f'quotation_{key}', 'sale.order',
                                  order_values(f'TP-PRESUPUESTO-{key.upper()}'), expected=expected)
        order = ensure_record(env, f'order_{key}', 'sale.order',
                              order_values(f'TP-EJEMPLO-{key.upper()}'), expected=expected)
        if order.state in ('draft', 'sent'):
            order.action_confirm()
        if order.state != 'sale':
            raise RuntimeError(f'El pedido de ejemplo {order.name} está cancelado; no se recreó.')
        if not order.picking_ids:
            raise RuntimeError(f'No se generó la entrega del pedido {order.name}.')
        for picking in order.picking_ids:
            if (picking.sale_channel_id != channels[key]
                    or picking.picking_type_id.warehouse_id != warehouses[key]):
                raise RuntimeError(f'La entrega de {order.name} no coincide con el canal y depósito.')
        if not order.invoice_ids:
            order._create_invoices()
        invoices = order.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice' and move.state != 'cancel')
        if not invoices:
            raise RuntimeError(f'No hay una factura activa en el pedido {order.name}; se conservó sin recrear.')
        if any(move.sale_channel_id != channels[key] or move.journal_id != journals[key] for move in invoices):
            raise RuntimeError(f'La factura de {order.name} no coincide con el canal y diario.')
        summary.append(
            f'{channels[key].name}: presupuesto {quotation.name}; pedido {order.name}; '
            f'entrega {", ".join(order.picking_ids.mapped("name"))}; '
            f'factura(s) ID {invoices.ids}, estado {", ".join(invoices.mapped("state"))}'
        )
    # Commit explicitly: Odoo shell rolls back by default on leaving the session.
    env.cr.commit()
    print('\nDATOS DE PRÁCTICA LISTOS')
    print('Usuario: tp_canales')
    if password:
        print(f'Contraseña generada: {password}')
        print('Guardá esta contraseña. Al repetir la carga se conserva, no se vuelve a mostrar.')
    else:
        print('Contraseña: la misma que se mostró en la primera ejecución (sin cambios).')
    print('Contabilidad de práctica: ' + str(company.chart_template))
    for line in summary:
        print(line)
    print('Las entregas no se validaron y las facturas nuevas se dejaron en borrador.')


try:
    load_demo(env)
except Exception:
    env.cr.rollback()
    raise
