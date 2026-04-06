from odoo import models, fields, api

class SaleOrderLineKsc(models.Model):
    _name = 'sale.order.line.ksc'
    _description = 'Sale Order Line'


    order_id = fields.Many2one('sale.order.ksc', string='Order')
    product_id = fields.Many2one('product.ksc', string='Product')
    name = fields.Text(string='Description')
    quantity = fields.Float(digits=(6, 2))
    unit_price = fields.Float(digits=(6, 2))
    uom_id = fields.Many2one('product.uom.ksc', string='Unit of Measure')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status')

    # ✅ Computed Subtotal (stored)
    subtotal_without_tax = fields.Float(
        string="Subtotal (No Tax)",
        compute="_compute_subtotal",
        store=True,
        digits=(6, 2)
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal_without_tax = (line.quantity or 0.0) * (line.unit_price or 0.0)

    # ✅ Onchange on product
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Fetch unit price and default quantity = 1"""
        for rec in self:
            if rec.product_id:
                rec.unit_price = rec.product_id.sale_price
                rec.quantity = 1.0
