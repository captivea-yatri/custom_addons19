# -*- coding: utf-8 -*-
{
    'name': 'Cap Group Services',
    'version': '19.0.0.1',
    'description': 'Custom module for Group Services',
    'depends': ['base', 'hr'],
    'data': [
         "security/ir.model.access.csv",
         "security/security.xml",
        'data/ir_ui_view.xml',
        'data/ir_actions_act_window.xml',
        'data/ir_ui_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
