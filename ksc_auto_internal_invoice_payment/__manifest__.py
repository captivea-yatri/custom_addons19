{
    'name': "Auto Internal Invoice Payment",
    'version': "19.0.0.0",
    'category': 'Accounting',
    'summary': "Module created automatic payment for internal company invoice.",
    'description': """
    Auto Internal Transaction Configuration.
    """,
    'depends': ['account', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'views/auto_internal_transaction_configuration.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
