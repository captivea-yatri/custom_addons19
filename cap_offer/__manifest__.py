# -*- coding: utf-8 -*-

{
    'name': "CAP Offer",
    'summary': """
        Sale The Offer
        """,
    'description': """
        Module is used for sale the specific offer. Based on the configuration, the offer will be set on the sale order.
        Same on project and task. If offer restrict time == True, then task will not be created manually.
        If order with order line contains offer with restrict time == True as well as restrict time == False, then user
        can not sale more then 25 hours for order line with offer with restrict time == False. and also no one can add 
        more timesheet then that.
    """,
    'author': "Captivea",
    'website': 'www.captivea.us',
    'category': 'Sale',
    'version': '19.0.0.1.0',
    'license': 'LGPL-3',
    'depends': ['sale', 'cap_domain', 'cap_project_test','ksc_sale_project_extended', 'access_rights_management'],
    'data': [
        "security/ir.model.access.csv",
        "views/offer.xml",
        "views/product_template.xml",
        "views/sale.xml",
        "views/project.xml",
        "views/res_config_settings.xml",
        "views/default_domain.xml",
        'wizard/link_project.xml',
        "views/project_task.xml",
        "views/res_company_views.xml",
        "views/business_unit.xml",
        "views/business_localisation.xml",
        "views/sale_order_template.xml",
    ],
    'installable': True,
    'auto_install': False,
}
