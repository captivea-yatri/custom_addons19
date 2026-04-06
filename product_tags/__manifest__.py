{
    "name": "Product Tags",
    "version": "19.0.0.1",
    "author": "Julius Network Solutions",
    "website": "http://julius.fr",
    "category": "Sales Management",
    "depends": ['product', 'sale'],
    "description": """
    Add tags in products like it's done for the partners
    """,
    "demo": [],
    "data": [
        'security/product_security.xml',
       'security/ir.model.access.csv',
       'views/product_view.xml',
    ],
    'installable': True,
}
