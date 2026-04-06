{
    'name': "Customer Payment Terms",
    'version': "19.0.0.0",
    'category': 'Accounting',
    'summary': "Advanced Features for Customer Payment Terms",
    'description': """ 
    Contains advanced features for Customer Payment Terms
    """,
    'depends': ['account', 'payment', 'sale'],
    'data': [
        'views/payment_term_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
