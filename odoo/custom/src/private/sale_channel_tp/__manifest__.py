{
    'name': 'TP - Canales de venta',
    'version': '19.0.1.0.0',
    'summary': 'Canales, depósitos y diarios para pedidos, entregas y facturas',
    'category': 'Sales/Sales',
    'author': 'Federico López',
    'license': 'AGPL-3',
    'depends': ['sale_management', 'sale_stock'],
    'data': [
        'security/sale_channel_security.xml',
        'security/ir.model.access.csv',
        'views/sale_channel_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
    ],
    'application': False,
    'installable': True,
}
