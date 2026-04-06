{
    "name": "CRM AI Dynamic Tagging",
    "version": "1.0",
    "summary": "AI-based dynamic CRM tag creation and website detection",
    "depends": ["crm"],  # Ensure crm module is installed
    "data": [
        # "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
    "author": "Your Name or Company",  # Ensure this is present
}