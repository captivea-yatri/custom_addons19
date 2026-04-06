# -*- coding: utf-8 -*-
{
    "name": "Project Feedback web",
    "version": "19.0.0.1",
    "category": "portal",
    'summary': 'website Feedback',
    "description": """Website feedback Description of the module.""",
    "price": 000,
    "currency": 'EUR',
    "depends": ['cap_project_feedback', 'portal', 'project'],
    "data": ["data/data.xml",
             "views/portal_my_projects.xml",
             "views/feedback_template.xml",
             "views/feedback_portal_views.xml",
             ],
"assets": {
    "web.assets_frontend": [
        "cap_project_feedback_web/static/src/js/zoom_fix.js",
    ],
    "web.assets_backend": [],
},

    "auto_install": False,
    "installable": True,
    "application": False,
    "license": 'LGPL-3',
}
