# Part of CAPTIVEA. Odoo 14 EE.

{
    "name": "Automatic Deferred Earnings",
    "version": "19.0.0.0",
    "author": "Captivea",
    "website": "https://www.captivea.com",
    "summary": "Add automatic deferred earnings account. Helps to create time credit revenue and related invoice",
    "description": "- Add change that helps to manage minimum sales price of the product."
                   "- In more one can have option to skip product from sale order line but it will be visible in invoice."
                   "and will also be managed by company",
    "depends": [
        'product', 'account_asset', 'base', 'ksc_sale_project_extended','sale_project',
    ],
    'license': 'LGPL-3',
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "security/security_time_credit.xml",
        "data/ir_cron/sale_order.xml",
        "data/ir_cron/account_asset.xml",
        "views/account_payment_views.xml",
        "views/res_company_views.xml",
        "views/account_assets_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/time_credit_views.xml",
        "views/res_users_views.xml",
        "views/res_partner_views.xml",
        "views/report_invoice.xml",
        "wizard/account_payment_register_views.xml"
    ],
}
