# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LinkSoProject(models.TransientModel):
    _inherit = 'link.so.project.wizard'

    project_ids = fields.Many2many('project.project', 'project_rel_ref', 'project_id', 'link_so_project')

    @api.onchange('operation')
    def update_project_on_date(self):
        sale_orders = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        project_ids = self.env['project.project']
        if (sale_orders.company_id.allow_offer_date and
                sale_orders.create_date.date() >= sale_orders.company_id.allow_offer_date):
            for rec in self:
                if rec.operation == 'link':
                    if sale_orders.offer_id:
                        project_with_offer_ids = self.env['project.project'].search([
                            ('company_id', '=', sale_orders.company_id.id)])
                        project_ids = project_with_offer_ids.filtered(lambda project: project.offer_id)
                    else:
                        project_ids = self.env['project.project'].search([
                            ('company_id', '=', sale_orders.company_id.id),
                            ('offer_id', '=', False)
                        ])
            if project_ids:
                rec.project_ids = [(6, 0, project_ids.ids)]
        else:
            self.project_ids = self.env['project.project'].search([])

    def link_so_project(self):
        """
        Create task with link so project which so order_line product offer restrict time == False.
        """
        sale_orders = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        if (sale_orders.company_id.allow_offer_date and
                sale_orders.create_date.date() >= sale_orders.company_id.allow_offer_date):
            if self.operation != 'create':
                if self.project_id and sale_orders.offer_id.restrict_time != self.project_id.offer_id.restrict_time:
                    raise ValidationError(
                        'Project offer restrict time is not compatible with sale order offer restrict time!')
                else:
                    self.with_context(link_so_project=True).create_project_task(sale_orders)
                    so_task_ids = self.env['project.task'].search([('project_id', '=', sale_orders.project_ids.id)])
                    sale_orders.sudo().tasks_ids = [[6, 0, so_task_ids.ids]]
        return super(LinkSoProject, self.with_context(link_so_project=True)).link_so_project()

    def create_project(self, sale_order):
        """
        Create task only those product which so order_line product offer restrict time == False.
        """
        res = super(LinkSoProject, self).create_project(sale_order)
        if (sale_order.company_id.allow_offer_date and
                sale_order.create_date.date() >= sale_order.company_id.allow_offer_date):
            self.create_project_task(sale_order)
        return res

    def create_project_task(self, sale_order):
        """
        Set the domain into default domain fields into project.project.
        Create task only those product which so order_line product offer restrict time == False.
        """
        domain_ids = sale_order.order_line.mapped('product_id').mapped('default_domain_ids')
        project_id = sale_order.mapped('order_line').mapped('project_id')
        if project_id:
            project_id.write({'default_domain_ids': [(4, domain.id) for domain in domain_ids.filtered(lambda d: d.all_phases == False)]})
            phase = project_id.phase_ids
            if phase:
                phase[0].write({'complementary_default_domain_ids': [(4, domain.id) for domain in
                                                         domain_ids.filtered(lambda d: d.all_phases == True)]})
        else:
            self.project_id.write({'default_domain_ids': [(4, domain.id) for domain in domain_ids.filtered(lambda d: d.all_phases == False)]})
            phase = self.project_id.phase_ids
            if phase:
                phase[0].write({'complementary_default_domain_ids': [(4, domain.id) for domain in
                                                                     domain_ids.filtered(
                                                                         lambda d: d.all_phases == True)]})
        restrict_time_false = sale_order.order_line.filtered(
            lambda so_line: so_line.product_id.offer_ids and so_line.product_id.offer_ids.filtered(lambda offer:offer.restrict_time == False))
        restrict_time_true = sale_order.order_line.filtered(
            lambda product: product.product_id.offer_ids and product.product_id.offer_ids.filtered(lambda offer:offer.restrict_time == True))

        if restrict_time_false and restrict_time_true and sale_order.offer_id.restrict_time == True:
            for line in restrict_time_false:
                task_values = {
                    'name': line.product_id.name,
                    'allocated_hours': line.product_uom_qty,
                    'project_id': line.project_id.id or self.project_id.id,
                    'default_domain_id': line.product_id.default_domain_ids[0].id
                    if line.product_id.default_domain_ids else False,
                    'sale_line_id': line.id
                }
                self.env['project.task'].create(task_values)