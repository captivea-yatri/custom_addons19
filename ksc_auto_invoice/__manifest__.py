# -*- coding: utf-8 -*-
{
    'name': 'KSC Auto Confirm Invoice',
    'summary': 'Create Invoice on validation of sale order if not Online Payment',
    'description': """Helps to create invoice, validate invoice and send it to customer on validation of sale order if order is not with online payment""",
    'category': 'sale',
    'version': '19.0.0.1',
    'sequence': 350,
    'depends': ['base','sale', 'sale_margin', 'sale_timesheet', 'account', 'mail', 'cap_account_intern_company_transection','timesheet_grid','project_forecast','sale_subscription','cap_partner'],
        #added a cap_partner module in depends for view inherit.
    'website': 'https://www.konsultoo.com',
    'author': "Konsultoo",
    'data': [
        'data/data.xml',
        'data/invoice_mail_template.xml',
        'security/security_deposit.xml',
        'views/account_move_views.xml',
        'views/sale_view.xml',
        'views/project_view.xml',
        'views/project_task_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
