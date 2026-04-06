from odoo import models, fields

class ProductKsc(models.Model):
    _name = "product.ksc"
    _description = "Products (KSC)"

    name = fields.Char(required=True)
    sku = fields.Char(required=True)
    weight = fields.Float(digits=(6, 2))
    length = fields.Float(digits=(6, 2))
    volume = fields.Float(digits=(6, 2))
    width = fields.Float(digits=(6, 2))
    barcode = fields.Char()

    product_type = fields.Selection(
        [('storable', 'Storable'),
         ('consumable', 'Consumable'),
         ('service', 'Service')],
        default='storable'
    )
    list_price = fields.Float(string='Price', default=1.00, digits=(6, 2))
    sale_price = fields.Float(default=1.00, digits=(6, 2))
    cost_price = fields.Float(default=1.00, digits=(6, 2))

    # category_id = fields.Many2one('product.category.ksc')
    uom_id = fields.Many2one('product.uom.ksc')
