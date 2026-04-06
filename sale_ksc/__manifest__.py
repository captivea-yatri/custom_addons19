{
    'name': "Sales KSC",
    'version': '1.0',
    'depends': ['base'],
    'author': "KSC",
    'category': 'Sales',
    'data': [
        'security/ir.model.access.csv',

        'views/menu.xml',
        'views/product_category_ksc.xml',
        'views/product_uom_category_ksc.xml',
        'views/product_uom_ksc.xml',
        'views/product_ksc.xml',
        'views/res_partner_ksc.xml',
        'views/sale_order_ksc.xml',
        'views/crm_team_ksc.xml',
        'views/crm_lead_ksc.xml',
        'views/crm_lead_line_ksc.xml',
        'views/stock_warehouse_ksc.xml',
    ],
    'installable': True,
    'application': True,
}
