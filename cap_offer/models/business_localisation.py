from odoo import fields, models, api,_

class BusinessLocalisation(models.Model):
    _name = 'business.localisation'

    name = fields.Char('Name')
    pricelist_ids = fields.Many2many('product.pricelist','rel_localisation_pricelist','pricelist_id','localisation',string="Pricelists")