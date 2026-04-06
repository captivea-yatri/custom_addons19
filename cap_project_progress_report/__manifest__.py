# -*- coding: utf-8 -*-
{
    'name': "Cap Project Progress Report",

    'summary': """
        Generate a Project Progress Report.
        """,

    'description': """
        Generate a Project Progress Report.
    """,

    'author': 'Captivea',
    'website': 'www.captivea.us',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'project',

    # any module necessary for this one to work correctly
    'depends': ['hr_timesheet', 'sale', 'ksc_sale_project_extended', 'ksc_project_extended',
                'ksc_project_go_live_maintainer', 'cap_requirements', 'web', 'sign'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/project_security.xml',
        'data/custom_mail_template.xml',
        'views/project_milestone_view.xml',
        'views/project_view.xml',
        'views/project_task_type_view.xml',
        'views/project_status_views.xml',
        'views/project_progress_view.xml',
        'report/project_progress_report.xml',
        'report/project_progress_report_no_deadline_template.xml',
        'report/project_progress_report_templates.xml',
        "views/project_domain_history_views.xml",
    ],
}
