# -*- coding: utf-8 -*-

{
    'name': 'Manage Project Go Live History',
    'summary': 'This module help to manage go live target. Were it will help to manage history, reason and prof to change the go live target.',
    'category': "Services/Project",
    'version': "19.0.0.0.0",
    "author": "Konsultoo Software Consulting PVT. LTD.",
    'maintainer': 'Konsultoo Software Consulting PVT. LTD.',
    'contributors': ["Konsultoo Software Consulting PVT. LTD."],
    'website': 'https://www.konsultoo.com/',
    'depends': ['project', 'base'],
    'data': [
        'security/go_live_change_request_security.xml',
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'views/go_live_change_request_views.xml',
        'views/res_company_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
