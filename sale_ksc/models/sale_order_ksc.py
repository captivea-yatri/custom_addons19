from odoo import models, fields, api

class SaleOrderKsc(models.Model):
    _name = 'sale.order.ksc'
    _description = 'Sale Order'

    name = fields.Char(required=True, string='Order No')
    customer_id = fields.Many2one(
        'res.partner.ksc',
        string='Customer',
        domain=[('parent_id', '=', False)],
        required=True
    )
    invoice_customer_id = fields.Many2one('res.partner.ksc', string='Invoice Customer')
    shipping_customer_id = fields.Many2one('res.partner.ksc', string='Shipping Customer')
    date_order = fields.Date(string='Order Date')
    order_line_ids = fields.One2many('sale.order.line.ksc', 'order_id', string='Order Lines')
    salesperson_id = fields.Many2one('res.users', string='Salesperson')
    lead_id = fields.Many2one('crm.lead.ksc', string='Leads')
    uom_id = fields.Many2one('product.uom.ksc', string='Unit of Measure')
    quantity=fields.Many2one('sale.order.line.ksc', string='Quantity')
    unit_price= fields.Many2one('sale.order.line.ksc', string='Unit Price')
    subtotal_without_tax= fields.Many2one('sale.order.line.ksc' )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status')

    # ✅ Computed Non-stored Fields
    total_weight = fields.Float(
        string="Total Weight",
        digits=(6, 2),
        compute="_compute_totals",
        store=False
    )
    total_volume = fields.Float(
        string="Total Volume",
        digits=(6, 2),
        compute="_compute_totals",
        store=False
    )

    # ✅ Stored computed total order amount
    order_total = fields.Float(
        string="Order Total",
        compute="_compute_order_total",
        store=True,
        digits=(6, 2)
    )

    @api.depends('order_line_ids.product_id.weight', 'order_line_ids.product_id.volume')
    def _compute_totals(self):
        """Compute total weight and volume"""
        for order in self:
            order.total_weight = sum(line.product_id.weight for line in order.order_line_ids if line.product_id)
            order.total_volume = sum(line.product_id.volume for line in order.order_line_ids if line.product_id)

    @api.depends('order_line_ids.subtotal_without_tax')
    def _compute_order_total(self):
        for order in self:
            order.order_total = sum(line.subtotal_without_tax for line in order.order_line_ids)

    # ✅ Auto-fill Invoice & Shipping Address on Customer Change
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        for rec in self:
            if rec.customer_id:
                invoice_child = rec.customer_id.child_ids.filtered(lambda c: c.address_type == 'invoice')
                shipping_child = rec.customer_id.child_ids.filtered(lambda c: c.address_type == 'shipping')

                rec.invoice_customer_id = invoice_child[:1].id if invoice_child else False
                rec.shipping_customer_id = shipping_child[:1].id if shipping_child else False
