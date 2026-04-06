# -*- coding: utf-8 -*-
{
    'name': 'Cap Cron Failure Notification',
    'version': '19.0.0.0',
    'description': 'Custom module for notifying when scheduled action get stuck',
    'depends': ['base','base_setup','mail'],
    'data': [
        "security/ir.model.access.csv",
        "views/cron_failure_history_view.xml",
        "views/res_config_settings_views.xml",

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
