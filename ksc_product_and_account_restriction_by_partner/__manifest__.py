{
    'name': "Product Account Restriction By Partner",
    'version': "19.0.0.0",
    'category': 'Accounting',
    'summary': "Product And Account Restriction by Partner",
    'description': """ 
    Product and Account Restriction by Partner.
    """,
    'depends': ['account', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_account_restriction_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
