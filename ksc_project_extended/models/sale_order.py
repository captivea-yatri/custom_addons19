# x_studio_block_timesheet_log

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_studio_block_timesheet_log = fields.Boolean(string='Block timesheet log')
    authorized_invoicing_amount = fields.Float(string='Authorized invoicing amount', tracking=True)
    not_invoiced_amount = fields.Float(string='Current logged amount not invoiced',
                                       compute='_compute_not_invoiced_amount')

    @api.constrains('authorized_invoicing_amount')
    def _check_authorized_invoicing_amount(self):
        """nsures the authorized invoicing amount is always a positive value."""
        if self.authorized_invoicing_amount < 0:
            raise ValidationError(_('Authorized invoicing amount must be positive number!!!'))

    def _compute_not_invoiced_amount(self):
        """Computes the not-invoiced amount for sale orders with an authorized invoicing limit.
For delivered-timesheet products, it recalculates the balance by subtracting invoiced
hours and adding consumed (logged) hours. If no relevant lines exist or authorization
is zero, the not-invoiced amount is reset to 0.0."""
        for order in self:
            if order.authorized_invoicing_amount > 0.00:
                order_line_ids = order.order_line.filtered(
                    lambda line: line.product_id.service_policy == 'delivered_timesheet')
                for order_line_id in order_line_ids:
                    order.not_invoiced_amount -= order_line_id.qty_invoiced * order_line_id.price_unit
                    order.not_invoiced_amount += order_line_id.x_studio_consumed_qty * order_line_id.price_unit
                if not order_line_ids:
                    order.not_invoiced_amount = 0.00
            else:
                order.not_invoiced_amount = 0.00
