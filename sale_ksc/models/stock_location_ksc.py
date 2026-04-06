from odoo import models, fields

class StockLocationKsc(models.Model):
    _name = 'stock.location.ksc'
    _description = 'Stock Location Ksc'

    name = fields.Char(string="WareHouse Name", required=True)
    parent_id = fields.Many2one(
        'stock.location.ksc',
        string="Parent Location",
    )
    location_type = fields.Selection(
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),

    )