# -*- coding: utf-8 -*-
{
    'name': "mrp_attachment",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.odoo.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '19.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mrp','mrp_workorder'],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
        'views/mrp.xml',
        'views/mo.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
