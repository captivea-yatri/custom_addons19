from odoo import models, fields

class ProductUomCategoryKsc(models.Model):
    _name = "product.uom.category.ksc"
    _description = "UOM Category (KSC)"

    name = fields.Char()
    # uom_ids = fields.One2many('product.uom.ksc', 'category_id', string="UOMs")
