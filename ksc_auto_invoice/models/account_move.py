# coding: utf-8
from odoo import _, api, fields, models
from collections import defaultdict
from odoo.tools import lazy


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cost = fields.Float('Cost')


    def unlink(self):
        """
        Overrides unlink to clear related timesheet links before deleting invoice lines.
        """
        move_line_read_group = self.env['account.move.line'].sudo().search_read([
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'draft'),
            ('sale_line_ids.product_id.invoice_policy', '=', 'delivery'),
            ('sale_line_ids.product_id.service_type', '=', 'timesheet'),
            ('id', 'in', self.ids)],
            ['move_id', 'sale_line_ids'])
        riss_invoice_ids_per_move = defaultdict(lambda: self.env['sale.order.line'])
        for move_line in move_line_read_group:
            riss_invoice_ids_per_move[move_line['move_id'][0]] += self.env['sale.order.line'].browse(
                move_line['sale_line_ids'])
        timesheet_read_group = self.sudo().env['account.analytic.line'].read_group([
            ('riss_invoice_id.move_type', '=', 'out_invoice'),
            ('riss_invoice_id.state', '=', 'draft'),
            ('riss_invoice_id', 'in', self.move_id.ids)],
            ['riss_invoice_id', 'so_line', 'ids:array_agg(id)'],
            ['riss_invoice_id', 'so_line'],lazy=False)

        timesheet_ids = []
        for timesheet in timesheet_read_group:
            move_id = timesheet['riss_invoice_id'][0]
            if timesheet['so_line'] and timesheet['so_line'][0] in riss_invoice_ids_per_move[move_id].ids:
                timesheet_ids += timesheet['ids']
        self.sudo().env['account.analytic.line'].browse(timesheet_ids).write({'riss_invoice_id': False})
        return super().unlink()


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_margin = fields.Monetary('Total Margin', compute='_compute_total_margin')
    timesheet_ress_group_ids = fields.One2many('account.analytic.line', 'riss_invoice_id', string='RISS Timesheet')
    timesheet_riss_total_duration = fields.Float(string='Hour', compute='_compute_timesheet_riss_total_duration')

    def _compute_total_margin(self):
        for rec in self:
            rec.total_margin = sum((line.price_subtotal - (line.cost * line.quantity)) for line in rec.invoice_line_ids)

    def _compute_timesheet_riss_total_duration(self):
        group_data = self.env['account.analytic.line'].read_group([
            ('riss_invoice_id', 'in', self.ids)
        ], ['riss_invoice_id', 'unit_amount'], ['riss_invoice_id'])
        timesheet_unit_amount_dict = defaultdict(float)
        timesheet_unit_amount_dict.update({data['riss_invoice_id'][0]: data['unit_amount'] for data in group_data})
        for invoice in self:
            total_time = invoice.company_id.project_time_mode_id._compute_quantity(
                timesheet_unit_amount_dict[invoice.id], invoice.timesheet_encode_uom_id)
            invoice.timesheet_riss_total_duration = round(total_time)

    def get_riss_group_timesheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Timesheet',
            'view_mode': 'list,form',
            'res_model': 'account.analytic.line',
            'domain': [('riss_invoice_id', '=', self.id)],
        }

    def action_post(self):
        for rec in self:
            if rec.move_type in ['out_invoice','out_refund']:
                return super(AccountMove,self.with_context(timesheet_validation=True)).action_post()
            else:
                return super(AccountMove,self).action_post()

    def write(self,vals):
        for rec in self:
            if rec.move_type in ['out_invoice','out_refund']:
                return super(AccountMove, self.with_context(timesheet_validation=True)).write(vals)
            else:
                return super(AccountMove, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.move_type in ['out_invoice','out_refund']:
                return super(AccountMove, self.with_context(timesheet_validation=True)).unlink()
            else:
                return super(AccountMove, self).unlink()
