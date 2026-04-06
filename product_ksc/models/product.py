from odoo import models, fields

class Product(models.Model):
    _name = 'product'
    _description = 'KSC Product'

    name = fields.Char(string="Product Name", required=True)
    sku = fields.Char(string="SKU")
    barcode = fields.Char(string="Barcode")
    can_be_sold = fields.Boolean(string="Can this product be sold?")

    product_type = fields.Selection(
        [
            ('storable', 'Storable'),
            ('consumable', 'Consumable'),
            ('service', 'Service')
        ],
        string="Product Type",
        default='storable'
    )

    sale_price = fields.Float(string="Sale Price", digits=(6, 2))
    cost_price = fields.Float(string="Cost Price", digits=(6, 2))

    active = fields.Boolean(string="Active", default=True)
    warehouse = fields.Char(string="Warehouse")
    product_image = fields.Image(string="Product Image")
    website_description = fields.Html(string="Website Description")
    internal_note = fields.Text(string="Internal Note")

