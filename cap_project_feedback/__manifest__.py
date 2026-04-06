# -*- coding: utf-8 -*-
{
    # TODO : test full after feedback_web
    "name": "Project Feedback",
    "version": "19.0.0.1",
    "category": "",
    'summary': 'customer Feedback',
    "description": """Project feedback Description of the module.""",
    "price": 000,
    "currency": 'EUR',
    "depends": ['hr', 'project', 'mail', 'cap_domain', 'cap_requirements'],
    "data": ["security/ir.model.access.csv",
             "data/email_template.xml",
             "views/project_feedback_views.xml",
             "views/project_view.xml",
             "views/project_task_view.xml",
             "views/project_domain_view.xml"
             ],
    "auto_install": False,
    "installable": True,
    "application": False,
    "license": 'LGPL-3',
}
