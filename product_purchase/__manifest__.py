# -*- coding: utf-8 -*-
{
    'name': "Product Purchase",

    'summary': """
        Porting of the Odoo11 "Purchases" button for products to bring up a list view of purchases for a product.
        """,

    'description': """
    """,

    'category': 'Uncategorized',
    'version': '19.0.0.1',

    'depends': ['base', 'purchase', 'product', 'portal'],

    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/portal.xml',
        'views/templates.xml',
    ],

    'demo': [
        'demo/demo.xml'
    ]
}
