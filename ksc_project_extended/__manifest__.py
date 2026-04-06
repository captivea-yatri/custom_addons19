# -*- coding: utf-8 -*-

{
    'name': 'Stop Changing Order Line on Task Log',
    'summary': 'Help to prevent from auto change of sale order line reference on task log that is exist. '
               'When change is made on task.',
    'category': "Services/Project",
    'version': "19.0.0.0",
    "author": "Konsultoo Software Consulting PVT. LTD.",
    'maintainer': 'Konsultoo Software Consulting PVT. LTD.',
    'contributors': ["Konsultoo Software Consulting PVT. LTD."],
    'website': 'https://www.konsultoo.com/',
    'depends': ['cap_partner', 'sale_timesheet_enterprise', 'hr', 'documents_project', 'base_automation', 'project_forecast'],
    'data': [
        'security/extra_timesheet_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data_task_color.xml',
        'data/custom_email_template.xml',
        'views/res_users.xml',
        'views/project_views.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/internal_project_quotas_views.xml',
        'views/hr_employee_views.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
