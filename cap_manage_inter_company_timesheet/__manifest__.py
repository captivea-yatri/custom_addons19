# -*- coding: utf-8 -*-
{
    'name': "Cap Manage Inter Company Timesheet",
    'summary': """Manages timesheet when employee works for other company project""",
    'description': """This module helps to overcome manual timesheet loging for both the company, in case employee is 
    working for other company. e.g., Employee A of France company is working for Project ABC of USA company. and when 
    Employee A loges timesheet on project ABC. System will create 1 more timesheet in France Company against USA company 
    project. System also make changes on update or delete on timesheet log.""",
    'author': "Captivea",
    'website': 'wwww.captivea.com',
    'category': 'Accounting/Accounting',
    'version': '19.0.0.1',
    'license': 'LGPL-3',
    'depends': ['project', 'timesheet_grid'],
    'data': [
        "views/project_task_inherit_view.xml",
        "views/account_analytic_line_inherit_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}
