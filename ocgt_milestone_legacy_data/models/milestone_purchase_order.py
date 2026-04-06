from odoo import models, fields

class MilestonePurchaseOrder(models.Model):
    _name = "milestone.purchase.order"
    _description = "Purchase Order"

    po_number = fields.Char(string="P.O. No", required=True)
    po_date = fields.Date(string="P.O. Date")
    partner_id = fields.Many2one('res.partner', string="Vendor Name")
    product_id = fields.Many2one('product.product', string="Product")
    internal_ref = fields.Char(string="Product Code", related="product_id.default_code", store=True)
    stock_code = fields.Char(string="Stock Code")
    product_description = fields.Char(string="Product Description")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    quantity = fields.Float(string="Quantity")
    basic_rate = fields.Float(string="Basic Rate")
    amount = fields.Float(string="Amount")
    received_quantity = fields.Float(string="Received Quantity")
    cancel_quantity = fields.Float(string="Cancel Quantity")
    balance_quantity = fields.Float(string="Balance Quantity")
    return_quantity = fields.Float(string="Return Quantity")


