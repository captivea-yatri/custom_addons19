from odoo import models, fields

class ProductUomKsc(models.Model):
    _name = "product.uom.ksc"
    _description = "Unit of Measure (KSC)"

    name = fields.Char()
    # category_id = fields.Many2one('product.uom.category.ksc')
