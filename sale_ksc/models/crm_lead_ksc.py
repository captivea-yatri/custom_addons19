from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CrmLeadKsc(models.Model):
    _name = 'crm.lead.ksc'
    _description = 'CRM Lead KSC'

    name = fields.Char(string="Lead Name", required=True)
    partner_id = fields.Many2one('res.partner.ksc', string="Customer")
    order_id = fields.One2many('sale.order.ksc', 'lead_id', string="Sales Orders", readonly=True)
    lead_line_ids = fields.One2many('crm.lead.line.ksc', 'lead_id', string="Lead Lines")

    state = fields.Selection([
        ('new', 'New'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ], string='Status', default='new')



    def action_mark_won(self):
        for lead in self:
            lead.state = 'won'

    def action_mark_lost(self):
        for lead in self:
            lead.state = 'lost'

    def action_generate_sales_quotation(self):
        for lead in self:
            if not lead.partner_id:
                raise UserError("Please select or create a Customer before generating a Sales Quotation.")

            # ✅ Create new quotation
            sale_order = self.env['sale.order.ksc'].create({
                'name': f'Quotation for {lead.name}',
                'customer_id': lead.partner_id.id,
                'lead_id': lead.id,
                'invoice_customer_id': lead.partner_id.id,
                'shipping_customer_id': lead.partner_id.id,
                'date_order': fields.Date.today(),
            })

            # ✅ Create quotation lines from lead lines
            for line in lead.lead_line_ids:
                unit_price = line.product_id.list_price or 0.0
                quantity = line.expected_sell_qty or 1
                subtotal = unit_price * quantity

                self.env['sale.order.line.ksc'].create({
                    'order_id': sale_order.id,
                    'product_id': line.product_id.id,
                    'name': line.name or line.product_id.name,
                    'uom_id': line.uom_id.id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal_without_tax': subtotal,
                })

            lead.order_id = [(4, sale_order.id)]

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order.ksc',
                'view_mode': 'form',
                'res_id': sale_order.id,
                'target': 'current',
            }