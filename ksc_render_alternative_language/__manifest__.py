# -*- coding: utf-8 -*-
{
    'name': "Render Alternative Language Translations",
    'summary': """This module helps to render alternative language translation.""",
    'description': """
        As when there is alternative language configured on any language and if the current language don't have the 
        translation it will load the translation of alternative language.
        
        Also if the translation is not for alternative language it will load from default language. 
    """,
    'author': 'Konsultoo Software Consulting PVT. LTD.',
    'maintainer': 'Konsultoo Software Consulting PVT. LTD.',
    'contributors': ["Konsultoo Software Consulting PVT. LTD."],
    'website': 'https://www.konsultoo.com/',
    'category': 'Hidden',
    'version': '19.0.0.1',
    'depends': ['base'],
    'data': [
        'views/res_lang_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
