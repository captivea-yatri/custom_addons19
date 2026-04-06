# -*- coding: utf-8 -*-
{
    'name': "Cap Partner",
    'summary': """
        Captivea representation of a partner
        """,
    'description': """
        Specific fields and views to manager partners
    """,
    'author': "Captivea",
    'website': 'www.captivea.us',
    'category': 'Project',
    'version': '19.0.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'website', 'project', 'account', 'ksc_sale_project_extended'],
    'data': [
        'data/project_status.xml',
        'security/cap_parnter_security.xml',
        'security/ir.model.access.csv',
        'data/cap_partner_activity.xml',
        'wizard/view_wiz_mark_customer_lost.xml',
        'views/rec_company_views.xml',
        'views/res_partner_view.xml',
        'views/account_move_views.xml',
        'views/report_invoice.xml',
        'views/project_status_view.xml',
        'views/account_analytic_line_views.xml',
        'views/project_inherit_views.xml',
        'views/sale_view.xml',
        'reports/sale_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
