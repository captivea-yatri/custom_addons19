{
    'name': 'Field Data Encryption',
    'version': '19.0.1.0.0',
    'summary': 'Encrypt selected stored fields dynamically',
    'category': 'Tools',
    'author': 'OpenClaw',
    'license': 'LGPL-3',
    'depends': ['base'],
    'external_dependencies': {
        'python': ['cryptography'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/field_encryption_rule_views.xml',
    ],
    'post_load': 'post_load',
    'installable': True,
    'application': False,
}
