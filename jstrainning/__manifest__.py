{
    'name': 'Custom Button on Homepage',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Adds a custom button to the homepage',
    'description': 'This module adds a custom button on the homepage of the Odoo website.',
    'author': 'Your Name',
    'depends': ['website'],
    'data': [
        'views/button_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/jstrainning/static/src/js/button.js',
        ],
    },
    'installable': True,
    'application': True,
}