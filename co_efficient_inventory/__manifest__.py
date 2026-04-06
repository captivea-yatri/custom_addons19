# -*- coding: utf-8 -*-
{
    'name': "efficient Inventory",

    'summary': """
        Modifications to inventory to provide custom Reporting Options
    """,

    'description': """
        Modifications to inventory to provide custom Reporting Options
    """,

    'category': 'Uncategorized',
    'version': '19.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/quant.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'auto_install': True,
}
