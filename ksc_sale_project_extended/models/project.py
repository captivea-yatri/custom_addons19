# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = 'project.project'

    sale_order_line_ids = fields.One2many('sale.order.line', 'project_id', string='Sale Order Lines')
    sale_order_ids = fields.One2many('sale.order', compute='_compute_sale_order', string='Sale Orders')
    accessible_so_line_ids = fields.One2many('sale.order.line', compute='_compute_access_so_line',
                                             string='Accessible Sale Order Line')
    label_studio_remaining_hours = fields.Char(default="Remaining Hours")

    def _compute_access_so_line(self):
        """Compute the all sale order lines accessible to the current record based on
    company and partner."""
        for rec in self:
            domain = []
            if self.company_id:
                domain.append(('company_id', '=', self.company_id.id))
            else:
                domain.append(('company_id', '=', self.env.user.company_id.id))
            company_ids = self.env['res.company'].sudo().search([])
            if self.partner_id.id not in company_ids.mapped('partner_id').ids:
                domain.append(('state', '=', 'sale'))
            sale_order_ids = self.env['sale.order'].sudo().search(domain)
            rec.accessible_so_line_ids = sale_order_ids.mapped('order_line')

    def _compute_sale_order(self):
        """
            Compute the sale orders related to the record through its sale order lines.
            This method maps the `sale_order_line_ids` of the record to their
            corresponding sale orders (`order_id`) and assigns them to
            `sale_order_ids`.
            """
        for record in self:
            record.sale_order_ids = record.sale_order_line_ids.mapped('order_id')

    @api.depends('allow_billable', 'partner_id.company_id')
    def _compute_partner_id(self):
        """
        Need to override the method because it checks and update partner id False.
        And we don't want to set partner id False in any conditions.
        """
        pass


    # def _compute_company_id(self):
    #     for project in self:
    #         # if a new restriction is put on the account or the customer, the restriction on the project is updated.
    #         res = super(AccountAnalyticLine, self)._compute_company_id()
    #         if not project.analytic_account_id.company_id:
    #             project.company_id = self.env.company
    #         return res

