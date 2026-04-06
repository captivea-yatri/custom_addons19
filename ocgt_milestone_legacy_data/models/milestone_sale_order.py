from odoo import models, fields

class MilestoneSaleOrder(models.Model):
    _name = "milestone.sale.order"
    _description = "Sales Order"

    so_number = fields.Char(string="S.O. No", required=True)
    so_date = fields.Date(string="S.O. Date")
    partner_id = fields.Many2one('res.partner', string="Client Name")
    parent_client_name = fields.Char(string="Parent Client Name")
    po_no = fields.Char(string="P.O. No")
    po_date = fields.Date(string="P.O. Date")
    product_id = fields.Many2one('product.product', string="Product")
    internal_ref = fields.Char(string="Product Code", related="product_id.default_code", store=True)
    stock_code = fields.Char(string="Stock Code")
    product_description = fields.Char(string="Product Description")
    uom_id = fields.Many2one('uom.uom', string="UOM")
    order_quantity = fields.Float(string="Order Quantity")
    rate = fields.Float(string="Rate")
    order_amount = fields.Float(string="Order Amount")
    do_quantity = fields.Float(string="D.O. Quantity")
    do_amount = fields.Float(string="D.O. Amount")
    pending_do_quantity = fields.Float(string="Pending D.O. Quantity")
    pending_do_amount = fields.Float(string="Pending D.O. Amount")
    invoice_quantity = fields.Float(string="Invoiced Quantity")
    invoice_amount = fields.Float(string="Invoice Amount")
    closed_quantity = fields.Float(string="Closed Quantity")
    closed_amount = fields.Float(string="Closed Amount")
    pending_invoice_quantity = fields.Float(string="Pending Invoice Quantity")
    pending_invoice_amount = fields.Float(string="Pending Invoice Amount")
    cost = fields.Float(string="Cost")
    cogs = fields.Float(string="COGS")
    client_on_hold = fields.Boolean(string="Client On Hold")
    client_hold_reason = fields.Char(string="Client Hold Reason")
    notation = fields.Char(string="Notation")
    zone = fields.Char(string="Zone")
    vehicle_no = fields.Char(string="Vehicle No")
    driver_name = fields.Char(string="Driver Name")





