# -*- coding: utf-8 -*-
{
    'name': "Co-efficient Manufacturing Reports",

    'summary': """
   it generates a report in an XLSX file of "BOM Cost Review".
        """,

    'description': """
    This module operates for the Bill of Materials (BOM) within MRP and also furnishes details when the 
    "BOM Cost Review" button is clicked. At that moment, it generates a report in an XLSX file.
    """,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '19.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mrp.xml',
        'views/bom.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
