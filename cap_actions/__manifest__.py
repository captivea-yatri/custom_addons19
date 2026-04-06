# -*- coding: utf-8 -*-
{
    'name': 'Cap Actions',
    'version': '19.0.0.1',
    'description': 'Custom module for generating actions to do',
    'depends': ['base', 'hr'],
    'data': [
        'security/cap_action_security.xml',
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
