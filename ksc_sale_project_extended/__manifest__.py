# -*- coding: utf-8 -*-

{
    'name': "Link or Create New Project From Sale Order",
    'summary': """Helps To Link Existing or Create New Project From Sale Order""",
    'description': """Helps to link existing project with the new sale order. 
    Also have a option to create new project.""",
    'author': "Konsultoo Software Consulting",
    'website': "https://www.konsultoo.com/",
    'category': 'Services/Project',
    'sequence': 99,
    'version': '19.0.0.0',
    'depends': ['sale_timesheet', 'sale_project', 'crm', 'account_followup','sale_subscription','sale_planning'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'security/security.xml',
        'views/product_views.xml',
        'wizard/link_so_project.xml',
        'views/view_sale_order.xml',
        'views/view_project.xml',
        'views/view_project_task.xml',
        'views/crm_lead_views.xml',
        'views/view_account_analytic.xml',
        'views/view_res_company.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

