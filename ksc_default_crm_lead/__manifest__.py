{
    'name': "Default CRM Lead Config",
    'version': "19.0.0.0",
    'category': 'Sales/CRM',
    'summary': "Advanced Features for Crm lead config",
    'description': """ 
    Contains advanced features for crm lead config
    """,
    'depends': ['crm', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/default_crm_lead_config_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
