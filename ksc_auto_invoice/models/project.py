from odoo import _, api, fields, models
from odoo.fields import Command
from odoo.tools import date_utils

class Project(models.Model):
    _inherit = 'project.project'

    invoice_for_groupe_riss = fields.Boolean(string='Invoice for Groupe Riss')

    def create_rss_invoice(self, project, order_line_ids):
        """
        create timesheet invoice for riss group company
        """
        today = fields.date.today()
        previous_month = date_utils.subtract(today, months=1)
        ending_prevs_month = date_utils.end_of(previous_month, "month")
        invoice_line_vals_list = []
        total_timesheet_ids = self.env['account.analytic.line']
        for order_line_id in order_line_ids:
            timesheet_ids = self.env['account.analytic.line'].search(
                [('date', '<=', ending_prevs_month),('so_line', '=', order_line_id.id),
                 ('unit_amount', '>', 0), ('riss_invoice_id', '=', False), ('project_id', '=', self.id)])
            if timesheet_ids:
                total_timesheet_ids += timesheet_ids
                invoice_line_vals = {
                    'product_id': order_line_id.product_id.id,
                    'analytic_distribution': False,
                    'quantity': sum(timesheet_ids.mapped('unit_amount')),
                    'company_id': self.env['res.company'].browse(6).id,
                    'tax_ids': False,
                    'sale_line_ids': [Command.link(order_line_id.id)],
                    'price_unit': order_line_id.price_unit,
                }
                invoice_line_vals_list.append((0,0,invoice_line_vals))
        if invoice_line_vals_list:
            move_vals = {
                'partner_id': self.partner_id.id,
                'invoice_date': ending_prevs_month,
                'move_type': 'out_invoice',
                'company_id': self.env['res.company'].browse(6).id,
                'currency_id': self.sale_order_id.currency_id.id,
                'invoice_payment_term_id': 16,
                'timesheet_ress_group_ids':[(4, t.id) for t in total_timesheet_ids],
                'line_ids':invoice_line_vals_list
            }
            invoice_id = self.env['account.move'].create(move_vals)
            if invoice_id:
                invoice_id.action_post()

    def generate_invoice_rss_group(self):
        """
        search project Invoice for Groupe Riss is True
        """
        project_ids = self.env['project.project'].search([('invoice_for_groupe_riss', '=', 'True')])
        for project in project_ids:
            order_line_ids = project.sale_order_line_ids.filtered(
                lambda sol: sol.product_id.service_policy == 'delivered_timesheet' and
                            sol.invoice_status == 'to invoice')
            if order_line_ids:
                project.create_rss_invoice(project, order_line_ids)
