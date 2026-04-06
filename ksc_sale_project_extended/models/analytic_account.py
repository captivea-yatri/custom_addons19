# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    tag_ids = fields.Many2many(related='task_id.tag_ids', string="Task tags", readonly=True)
    unit_price_from_so_line = fields.Float(string="Unit Price From SO Line in euro",
                                           compute="_compute_unit_price_from_so_line", store=True)

    def _compute_unit_price_from_so_line(self):
        """  Compute the analytic line unit price based on the linked sale order line by
    converting its rate to the group currency and multiplying by the analytic unit amount.
    Falls back to discounted unit price when hourly quantities are not available."""
        for rec in self:
            if rec.so_line and rec.unit_amount > 0:
                riss_group_currency = self.env['res.company'].browse(6).currency_id
                conversion_rate_from_so_curr_to_active_user_curr = self.env['res.currency']._get_conversion_rate(
                    from_currency=rec.so_line.currency_id, to_currency=riss_group_currency,
                    date=rec.date)
                if rec.so_line.x_studio_qty_in_hours != 0:
                    amount_in_so_currency = rec.so_line.price_subtotal / rec.so_line.x_studio_qty_in_hours
                    rec.unit_price_from_so_line = amount_in_so_currency * conversion_rate_from_so_curr_to_active_user_curr * rec.unit_amount
                else:
                    amount_in_so_currency = rec.so_line.price_unit - (
                                (rec.so_line.price_unit) * (rec.so_line.discount) / 100)
                    rec.unit_price_from_so_line = amount_in_so_currency * conversion_rate_from_so_curr_to_active_user_curr * rec.unit_amount
            else:
                rec.unit_price_from_so_line = 0.0

    def update_consume_qty(self):
        """ Update the sale order line's consumed hours by summing all related analytic
    line unit amounts except the current ones, and writing the total to
    `x_studio_consumed_qty`."""
        for record in self:
            so_line = record.so_line
            consumed_hours = 0.0
            for aline in self.env['account.analytic.line'].search([('so_line', '=', so_line.id),
                                                                   ('id', 'not in', self.ids)]):
                consumed_hours = consumed_hours + aline.unit_amount
            so_line.sudo().write({'x_studio_consumed_qty': consumed_hours})

    def unlink(self):
        self.update_consume_qty()
        return super(AccountAnalyticLine, self).unlink()

