from odoo import models, fields

class ProductCategoryKsc(models.Model):
    _name = "product.category.ksc"
    _description = "Product Category (KSC)"

    name = fields.Char(required=True)
    parent_id = fields.Many2one('product.category.ksc', string="Parent Category")
