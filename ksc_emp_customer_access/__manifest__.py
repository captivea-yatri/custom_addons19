# -*- coding: utf-8 -*-

{
    'name': 'Manage Customer access For Employee',
    'version': '19.0.0.1',
    'summary': 'Employee Management',
    'description': """Helps to manage employee access requests""",
    'category': 'Human Resources/Employees',
    'depends': ['base', 'mail', 'hr_expense', 'sale', 'sale_timesheet', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'data/emp_access_request.xml',
        'views/emp_access_request_views.xml',
        'views/res_partner_views.xml',
        'views/res_users_views.xml',
        'security/emp_konsultoo_security.xml',
        'views/integrated_access_request_view.xml',
        'views/sale_order_views.xml',
        'views/mail_activity_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
