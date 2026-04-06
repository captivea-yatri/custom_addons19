# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class LinkSoProject(models.TransientModel):
    _name = 'link.so.project.wizard'
    _description = "Create or Link Project From sale order"

    operation = fields.Selection([('create', 'Create New Project'),
                                  ('link', 'Link Existing Project')], required=True, default='create')
    project_id = fields.Many2one('project.project')

    def link_so_project(self):
        sale_order = self.env['sale.order'].browse(self.env.context.get('active_ids'))

        if self.operation == 'create':
            self.create_project(sale_order)
        else:
            for so_line in sale_order.order_line:
                if so_line.product_id.type == 'service' and not so_line.is_expense:
                    project = so_line.sudo()._timesheet_link_project(self.project_id)
                    sale_order.sudo().write({'project_account_id': project.account_id and project.account_id.id or False})
                    # INVOICE CREATION IS MOVED OUTSIDE FOR LOOP TO LINK ALL SO LINES TO ANALYTIC ACCOUNT BEFORE INVOICE CREATION
                    # sale_order.sudo().auto_invoice_confirm()

                    # so_line._timesheet_create_task(project=project)
                    if so_line.task_id:
                        msg_body = _("Task Created (%(name)s): %(link)s", name=so_line.product_id.name,
                                     link=so_line.task_id._get_html_link())
                        so_line.order_id.sudo().message_post(body_html=msg_body)
            sale_order.sudo().auto_invoice_confirm()
        # sale_order.linked_project = True

    def create_project(self, sale_order):
        for line in sale_order.order_line:
            if line.state == 'sale' and not line.is_expense:
                line.sudo().timesheet_service_generation_ksc()
                # if the SO line created a task, post a message on the order
                if line.task_id:
                    msg_body = _("Task Created (%(name)s): %(link)s", name=line.product_id.name,
                                 link=line.task_id._get_html_link())
                    line.order_id.message_post(body=msg_body)
        sale_order.sudo().auto_invoice_confirm()
