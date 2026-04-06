# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, fields, models, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    sale_order_line_ids = fields.One2many(related='project_id.sale_order_line_ids', string='Sale Order Lines')
    x_studio_development_completion_date = fields.Date(string='Development Completion Date')
    sale_line_id = fields.Many2one(
        'sale.order.line', 'Sales Order Item',
        copy=True, tracking=True, index='btree_not_null', recursive=True,
        compute='_compute_sale_line', store=True, readonly=False,
        domain="[]",
        help="Sales Order Item to which the time spent on this task will be added in order to be invoiced to your customer.\n"
             "By default the sales order item set on the project will be selected. In the absence of one, the last prepaid sales order item that has time remaining will be used.\n"
             "Remove the sales order item in order to make this task non billable. You can also change or remove the sales order item of each timesheet entry individually.")

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Override of mail.thread's message_new to initialize a project task
    created from an incoming email.
    Workflow:
        - Call the superclass implementation to create the task from the email.
        - If the created record is a `project.task`, assign its `sale_line_id`
          from the related project's `sale_line_id`."""
        res = super(ProjectTask, self).message_new(msg, custom_values)
        if res._name == 'project.task':
            res.sale_line_id = res.project_id.sale_line_id.id
        return res
