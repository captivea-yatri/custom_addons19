{
    'name': 'OCGT MILESTONE LEGACY',
    'version': '1.0',
    'category': 'Sales/Sales',
    'depends': ['base', 'product', 'uom'],
    'data': [
        'security/ir.model.access.csv',

        'views/milestone_purchase_order_views.xml',
        'views/milestone_sales_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'author': 'Captivea',
    'website': 'Captivea.com',
    'license': 'LGPL-3',
    'icon': 'ocgt_milestone_legacy_data/static/description/icon.png',
}
