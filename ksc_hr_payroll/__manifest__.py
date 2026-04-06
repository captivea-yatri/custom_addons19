# -*- coding: utf-8 -*-

{
    'name': 'Payroll Accounting Extended',
    'version': '19.0.0.1',
    'description': """
Payroll Accounting Feature.
==================================================

    * Automated Reconciliation
    * Direct Accounting Entry Visible
    """,
    'category': 'Human Resources/Payroll',
    'author': 'Konsultoo Software Consulting PVT. LTD.',
    'maintainer': 'Konsultoo Software Consulting PVT. LTD.',
    'contributors': ["Konsultoo Software Consulting PVT. LTD."],
    'website': 'https://www.konsultoo.com/',
    'depends': ['hr_payroll_account', 'hr_payroll', 'l10n_in_hr_payroll'],
    'data': ['data/data.xml',
             'views/hr_employee.xml',
             'views/hr_payslip.xml',
             'views/account_journal.xml',
             # 'views/hr_payslip_run_views.xml'
             ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
