# -*- coding: utf-8 -*-
{
    'name': 'CAP pdf package on quote',
    'summary': 'Attach pdf packages on email',
    'version': '19.0.0.0.1',
    'category': 'Sales/Sales',
    'description': """
    The related pdf packages linked with service type products on sale,
     will be attached in the email which is being set to customer. 
    """,
    'depends': ['product','base','sale_management','mail'],
    'author': "Captivea",
    'maintainer': "Captivea",
    'contributors': "Captivea",
    'website': 'https://www.captivea.com/',
    'data': ['views/pricelist_tree_view_inherit.xml'],
    'images': ['static/description/img/banner.gif', 'static/description/img/icon.png'],
    'price': 00,
    'currency': 'USD',
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': True,
}
