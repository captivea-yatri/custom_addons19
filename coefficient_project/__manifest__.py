# -*- coding: utf-8 -*-
{
    'name': "efficient Project",
    'summary': """
    Modifications to the default Odoo project management system to allow to the creation of project templates or the use of default stages.
        """,
    'description': """
    Modifications to the default Odoo project management system to allow to the creation of project templates or the use of default stages.
    """,
    'category': 'Project',
    'version': '19.0.0.1',
    'depends': ['base','project'],
    'data': [
        'data/project_type.xml',
        'views/project_view.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
}
