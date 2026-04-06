# -*- coding: utf-8 -*-
{
    'name': 'Project Test Portal',
     "version": "19.0.0.1",
    'description': "This module is used for customer access session test",
    'website': 'https://www.konsultoo.com/app/session_test_portal',
    "author": "Konsultoo Software Consulting PVT. LTD.",
    "category": "Extra Tools",
    "summary": "",
    'web.assets_frontend': [
        'cap_project_test_portal/static/src/scss/session_sharing_frontend.scss',
    ],
    'depends': ['portal', 'cap_project_test', 'web', 'sign'],
    'data': [
        "data/demo_sign_item.xml",
        "views/session_test_portal_view.xml",
        "views/session_test_report_action.xml",
        "views/session_test_views.xml",
        "views/session_test_portal_report.xml",
        "views/mail_template_view.xml",
        "views/test_view.xml",
    ],
    'web.assets_tests': [
        'cap_project_test_portal/static/tests/tours/session_test_tour.js',
    ],
    'web.report_assets_common': [
        'cap_project_test_portal/static/src/scss/default_font.scss',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
