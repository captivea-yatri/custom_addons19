{
    'name': "KSC Automatic Compensation",
    'version': "19.0.0.0",
    'category': "Accounting",
    'depends': ['account'],
    'author': 'konsultoo',
    'website': 'https://www.konsultoo.com/',
    'summary'
    'description': """
        For a contact, whether vendor/customer we can auto compensate the invoice and bills.
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'views/res_config_settings_views.xml',
        'wizard/auto_compensate_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
