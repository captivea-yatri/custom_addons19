# -*- coding: utf-8 -*-
{
    'name': "Cap Gamification",
    'summary': """
        No Goals will be deleted if domain is updated on challenge""",

    'description': """
        No Goals will be deleted if domain is updated on challenge""",

    'author': 'Captivea',
    'website': 'www.captivea.us',
    'version': '19.0.0.0',
    'category': 'Human Resources',
    # any module necessary for this one to work correctly
    'depends': ['gamification', 'hr', 'project', 'cap_partner'],

    # always loaded
    'data': [
        "views/gamification_goal_views.xml",
        "views/gamification_badge_view.xml",
        "views/hr_job_view.xml",
        'views/goals_history.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
