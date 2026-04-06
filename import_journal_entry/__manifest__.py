# -*- coding: utf-8 -*-
{
    'name': 'Import Journal Entry from CSV or Excel File',
    'version': '19.0.0.1',
    'sequence': 4,
    'category': 'Accounting',
    'summary': 'This modules helps to import journal entry transaction using CSV or Excel file',
    'description': """
    """,
    'author': 'Konsultoo.com',
    'website': 'http://www.konsultoo.com',
    'depends': ['base', 'account', 'sale_management'],
    'external_dependencies': {'python': ['unidecode']},
    'data': [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/account_move.xml"
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
