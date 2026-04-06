from odoo import models, fields

class StockWarehouseKsc(models.Model):
    _name = 'stock.warehouse.ksc'
    _description = 'Stock Warehouse Ksc'

    name = fields.Char(string="WareHouse Name", required=True)
    short_code = fields.Char(string="Short Code", required=True)
    address = fields.Many2one('res.partner.ksc', string="Address")


    view_location_id = fields.Many2one('stock.location.ksc', string="View Location" ,default="view" )