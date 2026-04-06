# -*- coding: utf-8 -*-

from odoo import api, models, fields, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import requests
import json


class Project(models.Model):
    _inherit = "project.project"

    use_documents = fields.Boolean("Use Documents", default=False)

    active = fields.Boolean('Active', default=True, tracking=True)
    color = fields.Integer(string='Color Index', compute='compute_project_color_remaining_hours', store=True)
    no_pm_report = fields.Boolean(string="Exclude for PM Report", tracking=True)
    report_frequency_in_days = fields.Integer(string="Report Frequency", default=7)

    business_analyst_ids = fields.Many2many(comodel_name='res.users', relation='res_users_business_analyst_rel',
                                            string="Business Analyst", tracking=True, domain=lambda self: [
            ('group_ids', '=', self.env.ref('base.group_user').id)])
    developers_ids = fields.Many2many(comodel_name='res.users', relation='res_users_developers_rel',
                                      string="Developers", tracking=True, domain=lambda self: [
            ('group_ids', '=', self.env.ref('base.group_user').id)])
    configurators_ids = fields.Many2many(comodel_name='res.users', relation='res_users_configurators_rel',
                                         string="Configurators", tracking=True, domain=lambda self: [
            ('group_ids', '=', self.env.ref('base.group_user').id)])
    architect_ids = fields.Many2many(comodel_name='res.users', relation='res_architect_users_rel',
                                     string="Architect", tracking=True, domain=lambda self: [
            ('group_ids', '=', self.env.ref('base.group_user').id)])
    attachment_ids = fields.Many2many('ir.attachment', 'doc_project_sprint_report_rel', 'project_id', 'doc_id',
                                      string="Sprint Meeting Report")
    exclude_for_production_review = fields.Boolean(string="Exclude for Production Review", tracking=True)
    exclude_for_go_live = fields.Boolean(string="Exclude for Go live Quality Issue", tracking=True)
    exclude_for_tests = fields.Boolean(string="Exclude for Tests Quality Issue", tracking=True)
    exclude_for_feedback = fields.Boolean(string="Exclude for Feedback Quality Issue", tracking=True)
    restrict_manual_timesheet = fields.Boolean(string="Restrict Manual Timesheet")
    x_studio_remaining_hours = fields.Float("Remaining hours", readonly=True,
                                            compute="compute_project_color_remaining_hours",
                                            store=True)
    on_hold_reason = fields.Selection([('no_hours', 'No Hours'), ('conflict', 'Conflict'),
                                       ('waiting_customer', 'Waiting Customer'),
                                       ('in_late_for_payment', 'In Late For Payment')], 'On Hold Reason', store=True,
                                      compute='compute_project_color_remaining_hours', tracking=True)
    partner_salesperson = fields.Many2one('res.users', string='Salesperson', related='partner_id.user_id')

    def get_followup_status(self, partner_id):
        """
        This function code is picked from default odoo as the followup status was working on company basis.
        where if company A has followup status in_need_action and company B has followup status no_action_needed.
        But when status is computed from company A. it changes color of Company B's task to red. and vice versa.
        To overcome this issue we have added below code.
        """
        today = fields.Date.context_today(self)
        followup_lines_info = partner_id.sudo().with_company(self.company_id)._get_followup_lines_info()
        max_followup = partner_id.sudo().with_company(self.company_id)._included_unreconciled_aml_max_followup()
        max_aml_delay = max_followup.get('max_delay') or 0
        next_followup_delay = max_followup.get('next_followup_delay') or 0
        has_overdue_invoices = max_followup.get('has_overdue_invoices')
        most_delayed_aml = max_followup.get('most_delayed_aml')

        # computation of followup_status
        followup_status = 'no_action_needed'
        if has_overdue_invoices and most_delayed_aml:
            followup_status = 'with_overdue_invoices'
        next_followup_date_exceeded = today >= partner_id.with_company(self.company_id).followup_next_action_date \
            if partner_id.with_company(self.company_id).followup_next_action_date else True
        if max_aml_delay > next_followup_delay and next_followup_date_exceeded and followup_lines_info:
            followup_status = 'in_need_of_action'

        total_overdue = 0
        for aml in partner_id.with_company(self.company_id).unreconciled_aml_ids:
            # and not aml.blocked
            if aml.company_id.id == self.company_id.id:
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                if is_overdue:
                    total_overdue += aml.amount_residual
        return followup_status, total_overdue

    def get_not_paid_invoice_ids(self):
        """
        Returns all outstanding customer invoices for the partner and its child contacts.
It collects posted customer invoices belonging to the same company and filters
those that are unpaid or partially paid with a valid due date. Used to identify
pending receivables for follow-up or validation checks.
        """
        parent_id = self.partner_id.mapped('parent_id') or self.partner_id
        invoice_ids = parent_id.invoice_ids + parent_id.mapped('child_ids').invoice_ids
        not_paid_invoice_ids = invoice_ids.filtered(
            lambda move: move.state == 'posted' and move.move_type == 'out_invoice' and
                         move.payment_state in ['not_paid', 'partial'] and move.invoice_date_due != False and
                         move.company_id.id == self.company_id.id)
        return not_paid_invoice_ids

    def send_mail(self):
        """
        Sends follow-up emails to the salesperson when a customer exceeds the allowed
late-payment grace period. It identifies overdue invoices per customer and
notifies the responsible salesperson with details of the delay and required
actions. This is triggered only when company-defined authorization rules permit
timesheet logging despite late payments.
        """
        partner_projects = []
        unique_combinations = []
        all_projects = self.search([('partner_id', '!=', False), '|', ('project_status_id', '=', False),
                                    ('project_status_id.code', 'not in', ['internal', 'internal_p2p3'])])
        for project in all_projects:
            tup = (project.partner_id, project, project.company_id)
            combination = (tup[0], tup[2])
            if combination not in unique_combinations:
                unique_combinations.append(combination)
                partner_projects.append(tup)
        for project in partner_projects:
            rec = project[1]
            today = date.today()
            parent_id = rec.partner_id.mapped('parent_id') or rec.partner_id
            invoice_ids = parent_id.invoice_ids + parent_id.mapped('child_ids').invoice_ids
            not_paid_invoice_ids = invoice_ids.filtered(
                lambda move: move.state == 'posted' and move.move_type == 'out_invoice' and
                             move.payment_state in ['not_paid', 'partial'] and move.invoice_date_due != False and
                             move.invoice_date_due < today and move.company_id.id == rec.company_id.id)
            if (rec.company_id.number_of_days_authorized_in_late and not_paid_invoice_ids and rec.partner_id.user_id
                    and rec.partner_id.user_id.partner_id.email):
                if today <= min(not_paid_invoice_ids.mapped('invoice_date_due')) + timedelta(
                        days=rec.company_id.number_of_days_authorized_in_late):
                    late_days = today - min(not_paid_invoice_ids.mapped('invoice_date_due'))
                    mail_pool = self.env['mail.mail']
                    values = {}
                    values.update({'subject': 'Followup to customer ' + rec.partner_id.name + ' for late in payment',
                                   'email_to': rec.partner_id.user_id.partner_id.email,
                                   # 'email_cc': rec.partner_id.user_id.employee_id.parent_id.user_id.partner_id.email
                                   })
                    min_due_date = not_paid_invoice_ids.mapped('invoice_date_due')[0]
                    for not_paid_invoice_id in not_paid_invoice_ids:
                        if not_paid_invoice_id.invoice_date_due < min_due_date:
                            min_due_date = not_paid_invoice_id.invoice_date_due
                            values.update({'body_html': """Hello """ + rec.partner_id.user_id.partner_id.name + """, <br/> <br/>
                                           The customer """ + rec.partner_id.name + """ is in late for """ + str(
                                late_days.days) + """ days with invoice """ + not_paid_invoice_id.name +
                                                        """ for """ + not_paid_invoice_id.company_id.name +
                                                        """. <br/> <br/> Please do the following step: <br/>
                                                            - Contact the customer and gather information about the payment. <br/>
                                                            - Log a comment on the customer. <br/>
                                                            - Create a task to your manager to ask him to Unblock the situation. """})
                        else:
                            values.update({'body_html': """Hello """ + rec.partner_id.user_id.partner_id.name + """, <br/> <br/>
                                            The customer """ + rec.partner_id.name + """ is in late for """ + str(
                                late_days.days) + """ days with invoice """ + not_paid_invoice_ids[0].name +
                                                        """ for """ + not_paid_invoice_id.company_id.name +
                                                        """. <br/> <br/> Please do the following step: <br/>
                                                            - Contact the customer and gather information about the payment. <br/>
                                                            - Log a comment on the customer. <br/>
                                                            - Create a task to your manager to ask him to Unblock the situation. """})
                    followup_status, total_overdue = rec.get_followup_status(parent_id)
                    if not parent_id.x_studio_authorize_to_log_hours_with_late_invoice:
                        msg_id = mail_pool.create(values)
                        if msg_id:
                            mail_pool.send([msg_id])
                    elif parent_id.x_studio_authorize_to_log_hours_with_late_invoice and parent_id.x_studio_authorize_late_amount < total_overdue:
                        msg_id = mail_pool.create(values)
                        if msg_id:
                            mail_pool.send([msg_id])

    @api.onchange('on_hold_reason')
    def onchange_on_hold_reason(self):
        """
        Here, we check and set on hold reason,
        if all hours are consumed then on hold reason is set as no_hours
        if any invoice is due then on hold reason is set as in_late_for_payment
        """
        if self.partner_id:
            company_ids = self.env['res.company'].sudo().search([])
            parent_id = self.partner_id.mapped('parent_id') or self.partner_id
            not_paid_invoice_ids = self.sudo().get_not_paid_invoice_ids()
            followup_status, total_overdue = self.get_followup_status(parent_id)
            if (self.sale_order_line_ids and
                    not any(so_line_id.product_id.service_policy != 'ordered_prepaid'
                            for so_line_id in self['sale_order_line_ids']) and round(self.x_studio_remaining_hours,
                                                                                     2) <= 0.0
                    and (self.partner_id.id not in company_ids.mapped('partner_id').ids and
                         self.partner_id.id != self.company_id.partner_id.id)):
                self.on_hold_reason = 'no_hours'
            elif self.on_hold_reason == 'no_hours':
                self.on_hold_reason = False
            elif ((not_paid_invoice_ids and followup_status in ['in_need_of_action', 'with_overdue_invoices'] and
                   fields.Date.today() > (min(not_paid_invoice_ids.mapped('invoice_date_due'))
                                          + timedelta(days=self.company_id.number_of_days_authorized_in_late)) and
                   not parent_id.x_studio_authorize_to_log_hours_with_late_invoice) or (
                          parent_id.x_studio_authorize_to_log_hours_with_late_invoice and
                          parent_id.x_studio_authorize_late_amount < total_overdue)):
                self.on_hold_reason = 'in_late_for_payment'

    @api.depends('sale_order_line_ids.x_studio_remaining_quantity', 'sale_order_line_ids.x_studio_consumed_qty',
                 'sale_order_line_ids', 'sale_order_line_ids.order_id.x_studio_block_timesheet_log',
                 'partner_id.x_studio_authorize_late_amount', 'partner_id.followup_status',
                 'partner_id.parent_id.x_studio_authorize_to_log_hours_with_late_invoice',
                 'partner_id.x_studio_authorize_to_log_hours_with_late_invoice', 'partner_id.total_overdue',
                 'on_hold_reason', 'partner_id.invoice_ids.payment_state', 'sale_order_line_ids.state')
    def compute_project_color_remaining_hours(self):
        """This compute method updates remaining hours, project color, and hold reasons based on sales lines, invoice status, customer follow-up, and consumed time.
It assigns red, orange, or default colors depending on overdue invoices, blocked timesheet logging, consumed hours, and authorization rules.
It also sets or clears on_hold_reason (like no_hours or in_late_for_payment) based on the business logic."""
        company_ids = self.env['res.company'].sudo().search([])
        for rec in self.filtered(lambda project: project.partner_id):
            # Set remaining hours
            hours = 0
            if len(rec['sale_order_line_ids']) > 0:
                hours = sum(line['x_studio_remaining_quantity'] for line in rec['sale_order_line_ids'].filtered(
                    lambda line: line.order_id.state in ['sale', 'lock']
                ))
            rec['x_studio_remaining_hours'] = hours

            if (rec.partner_id.id not in company_ids.mapped('partner_id').ids
                    and rec.partner_id.id != rec.company_id.partner_id.id):
                if (len(rec['sale_order_line_ids']) > 0 and
                        not any(so_line_id.product_id.service_policy != 'ordered_prepaid'
                                for so_line_id in rec['sale_order_line_ids'])):
                    if round(hours, 2) <= 0:
                        rec.write({'on_hold_reason': 'no_hours'})
                    elif round(hours, 2) > 0 and rec['on_hold_reason'] == 'no_hours':
                        rec['on_hold_reason'] = False

            if rec.on_hold_reason not in ['in_late_for_payment', False]:
                rec.write({'color': 1})
                continue
            parent_id = rec.partner_id.mapped('parent_id') or rec.partner_id
            today = date.today()

            # Get not paid invoices of customer.
            not_paid_invoice_ids = rec.sudo().get_not_paid_invoice_ids()

            # Get the followup status and total overdue of the company of which the task is.
            followup_status, total_overdue = rec.get_followup_status(parent_id)

            ################################### RED COLOR TIME CONSUMED ################################################
            sale_line_ids = rec.sale_order_line_ids.filtered(
                lambda line: line.product_id.service_policy == 'ordered_prepaid' and
                             line.product_id.x_studio_product_to_receive)
            if (sale_line_ids and len(sale_line_ids) == len(sale_line_ids.filtered(
                    lambda line: round(line.x_studio_consumed_qty, 2) >= round(line.x_studio_qty_in_hours, 2))) and
                not_paid_invoice_ids and followup_status in ['in_need_of_action', 'with_overdue_invoices']) and not any(
                sale_order_line_id.product_id.service_policy != 'ordered_prepaid' for sale_order_line_id in
                rec.sale_order_line_ids):
                rec.write({'color': 1, 'on_hold_reason': 'in_late_for_payment'})
                continue

            ################################### RED COLOR INVOICE LATE #################################################
            # If partner(customer)'s followup_status in ['in_need_of_action', 'with_overdue_invoices'] and not authorize
            # to log hours on
            # late invoice it will indicate to red color as one should not log.
            if followup_status in ['in_need_of_action', 'with_overdue_invoices']:
                if not parent_id.x_studio_authorize_to_log_hours_with_late_invoice:
                    if (not_paid_invoice_ids and any(inv_due_date < today for inv_due_date in
                                                     not_paid_invoice_ids.mapped('invoice_date_due') if
                                                     inv_due_date) and today > (
                            min(not_paid_invoice_ids.mapped('invoice_date_due'))
                            + timedelta(days=rec.company_id.number_of_days_authorized_in_late))):
                        rec.write({'color': 1, 'on_hold_reason': 'in_late_for_payment'})
                        continue
                if not_paid_invoice_ids and today > (min(not_paid_invoice_ids.mapped('invoice_date_due')) + timedelta(
                        days=rec.company_id.number_of_days_authorized_in_late)):
                    if parent_id.x_studio_authorize_to_log_hours_with_late_invoice and total_overdue > parent_id.x_studio_authorize_late_amount and today > (
                            min(not_paid_invoice_ids.mapped('invoice_date_due')) + timedelta(
                        days=rec.company_id.number_of_days_authorized_in_late)):
                        rec.write({'color': 1, 'on_hold_reason': 'in_late_for_payment'})
                        continue

            # If sale order is blocked any way task will have red indication
            if rec.sale_order_line_ids.mapped('order_id').filtered(
                    lambda order: order.state not in ['draft', 'cancel',
                                                      'sent'] and order.x_studio_block_timesheet_log):
                rec.write({'color': 1, 'on_hold_reason': False})
                continue

            ############################## ORANGE COLOR INVOICE LATE ###############################################
            # Invoice is due in less than 5 days --> Color is Orange
            # "Invoice is going to be due, ask customer to make payment!"
            day_left = today + timedelta(days=5)
            if rec.partner_id.id not in company_ids.mapped('partner_id').ids or \
                    parent_id.id not in company_ids.mapped('partner_id').ids:

                if (parent_id.x_studio_authorize_to_log_hours_with_late_invoice and
                        total_overdue <= parent_id.x_studio_authorize_late_amount and
                        followup_status in ['in_need_of_action', 'with_overdue_invoices']):
                    rec.write({'color': 2, 'on_hold_reason': False})
                    continue

                if not_paid_invoice_ids and (min(not_paid_invoice_ids.mapped('invoice_date_due')) < today) and (
                        min(not_paid_invoice_ids.mapped('invoice_date_due')) + timedelta(
                    days=rec.company_id.number_of_days_authorized_in_late)) >= today:
                    rec.write({'color': 2, 'on_hold_reason': False})
                    continue

                if not_paid_invoice_ids and any(date_due < day_left for date_due in
                                                not_paid_invoice_ids.mapped('invoice_date_due')):
                    rec.write({'color': 2, 'on_hold_reason': False})
                    continue

            ################################### ORANGE COLOR TIME CONSUMED #########################################
            if sale_line_ids and 0 < sum(round(line.x_studio_remaining_quantity, 2) for line in sale_line_ids) < 10:
                rec.write({'color': 2, 'on_hold_reason': False})
                continue
            rec.write({'color': 10, 'on_hold_reason': False})

    def action_view_tasks_from_project(self):
        """Open tasks related to the project with tree view as default."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'list,form,kanban,gantt,calendar,map,pivot,graph,activity',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_project_settings(self):
        """Opens the project settings form view for the current project,
        forcing the action to load this project's record directly."""
        action = self.env['ir.actions.act_window']._for_xml_id('project.open_view_project_all')
        action['domain'] = [('id', '=', self.id)]
        form_view = self.env['ir.model.data']._xmlid_to_res_id('project.edit_project')
        action['views'] = [(form_view, 'form'), (False, 'kanban'), (False, 'list'), (False, 'graph')]
        action['res_id'] = self.id
        action['target'] = 'current'
        return action


class Task(models.Model):
    _inherit = "project.task"

    color = fields.Integer(string='Color Index', compute='compute_task_color', store=True, default='10')
    warning_msg = fields.Char(string='Message', compute='compute_task_color', store=True)
    date_to_validate_production = fields.Date('To validate in Production Stage',
                                              compute='_compute_validate_production_stage_date', store=True)
    color_state = fields.Selection([('red', 'red'), ('orange', 'orange'), ], string="color state",
                                   compute='compute_task_color', store=True)
    restrict_manual_timesheet = fields.Boolean(related='project_id.restrict_manual_timesheet', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides task creation to auto-set the project, partner, and assigned users.
        Ensures tasks created via email or portal have the correct default project.
        Also assigns the project’s customer and default responsible user when missing."""
        # Task default partner mainly task created via email
        self = self.with_user(SUPERUSER_ID)
        ctx_project_id = self.env.context.get('default_project_id', False)
        ctx_active_id = self.env.context.get('active_id', False)
        for vals in vals_list:
            # code to portal user, if not project id in context then we set project id from default_project_id
            if not vals.get('project_id', False):
                if ctx_project_id and ctx_active_id and (ctx_project_id == ctx_active_id):
                    project_id = self.env['project.project'].browse(ctx_project_id)
                    vals.update({'project_id': project_id.id} if project_id else {'project_id': False})
            if vals.get('project_id', False):
                project_id = self.env['project.project'].browse(vals.get('project_id'))
                if project_id.partner_id and (not vals.get('partner_id', False) or
                                              vals.get('partner_id') != project_id.partner_id.id):
                    vals.update({'partner_id': project_id.partner_id.id})
            # Task default assignation
            if (not vals.get('user_ids', False) or vals.get('user_ids') == [[6, False, []]]) and vals.get('project_id'):
                project_id = self.env['project.project'].browse(vals.get('project_id'))
                vals.update({'user_ids': [(6, False, [project_id.user_id.id])] if project_id.user_id else False})
        return super(Task, self).create(vals_list)

    def write(self, vals):
        """ Overrides write to enforce default task assignment rules.
        If users are removed and the project has a default user,
        the task is automatically reassigned to the project's responsible user."""
        self = self.with_user(SUPERUSER_ID)
        if vals.get('user_ids') and self.project_id and self.project_id.user_id:
            users = sorted(vals.get('user_ids'), key=lambda x: x[1])
            user2 = sorted([[3, user.id] for user in self.user_ids], key=lambda x: x[1])
            if users == user2:
                vals.update({'user_ids': [(6, False, [self.project_id.user_id.id])]})
        return super(Task, self).write(vals)

    def get_task_color(self, partner_id, task_id):
        """
        1) We use this function in Automated Action 'check timesheet log creation' to decide user is able to log
        a timesheet on task or not.
        2) We also use this method in color compute function of task to identify task color is red or not.
        """
        today = date.today()
        parent_id = partner_id.mapped('parent_id') or partner_id
        invoice_ids = parent_id.invoice_ids + parent_id.mapped('child_ids').invoice_ids
        not_paid_invoice_ids = invoice_ids.filtered(
            lambda move: move.state == 'posted' and move.move_type == 'out_invoice' and
                         move.payment_state in ['not_paid', 'partial'] and move.invoice_date_due != False and
                         move.company_id.id == task_id.company_id.id)
        if not_paid_invoice_ids:
            if today > (min(not_paid_invoice_ids.mapped('invoice_date_due')) +
                        timedelta(days=task_id.company_id.number_of_days_authorized_in_late)):
                return 1
        else:
            return 10

    def get_followup_status(self, partner_id):
        """
        This function code is picked from default odoo as the followup status was working on company basis.
        where if company A has followup status in_need_action and company B has followup status no_action_needed.
        But when status is computed from company A. it changes color of Company B's task to red. and vice versa.
        To overcome this issue we have added below code.
        """
        today = fields.Date.context_today(self)
        followup_lines_info = partner_id.with_company(self.company_id)._get_followup_lines_info()
        max_followup = partner_id.with_company(self.company_id)._included_unreconciled_aml_max_followup()
        max_aml_delay = max_followup.get('max_delay') or 0
        next_followup_delay = max_followup.get('next_followup_delay') or 0
        has_overdue_invoices = max_followup.get('has_overdue_invoices')
        most_delayed_aml = max_followup.get('most_delayed_aml')

        # computation of followup_status
        followup_status = 'no_action_needed'
        if has_overdue_invoices and most_delayed_aml:
            followup_status = 'with_overdue_invoices'
        next_followup_date_exceeded = today >= partner_id.with_company(self.company_id).followup_next_action_date \
            if partner_id.with_company(self.company_id).followup_next_action_date else True
        if max_aml_delay > next_followup_delay and next_followup_date_exceeded and followup_lines_info:
            followup_status = 'in_need_of_action'

        total_overdue = 0
        for aml in partner_id.with_company(self.company_id).unreconciled_aml_ids:
            # and not aml.blocked
            if aml.company_id.id == self.company_id.id:
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                if is_overdue:
                    total_overdue += aml.amount_residual
        return followup_status, total_overdue

    @api.depends('stage_id')
    def _compute_validate_production_stage_date(self):
        """Computes the date when a task enters production-validation stage (stage ID 292).
Searches message and tracking logs to find the exact date the stage changed.
If found, sets that date; otherwise sets today, or clears the field when not in that stage.
"""
        # TODO : Need to check in database
        for rec in self:
            if rec.stage_id.id == 292:
                message_id = self.env['mail.message'].search(
                    [('model', '=', 'project.task'), ('res_id', '=', rec.id), ('subtype_id', '=', 52)], order='id desc',
                    limit=1)
                mail_tracking_value_id = self.env['mail.tracking.value'].search(
                    [('mail_message_id', '=', message_id.id), ('new_value_integer', '=', 292)])
                if mail_tracking_value_id:
                    rec.date_to_validate_production = mail_tracking_value_id.create_date.date()
                else:
                    # rec.date_to_validate_production = fields.Date.today() + relativedelta(day=1)
                    rec.date_to_validate_production = fields.Date.today()
            else:
                rec.date_to_validate_production = ''

    @api.constrains('allocated_hours')
    def onchange_planned_hours(self):
        """Ensures tasks always have positive allocated hours at creation or update.
"""
        context = dict(self.env.context)
        if 'check_initial_plan_hours' in context.keys() and context.get('check_initial_plan_hours'):
            for rec in self:
                if rec.allocated_hours <= 0 and rec.project_id.allow_timesheets:
                    raise ValidationError('Allocated hours must be greater than 0.')

    @api.onchange('partner_id', 'project_id')
    def onchange_partner_project(self):
        """Triggers when partner_id or project_id changes on a task.
Restricts available sale order lines based on service, tracking, and state conditions.
Returns a domain that limits selectable sale_line_id to valid service-related SO lines."""
        domain = [('id', 'in', self.sale_order_line_ids.ids), ("x_studio_service_tracking", "!=", "no"),
                  ("is_service", "=", True), ("is_expense", "=", False), ("state", "in", ['sale', 'done'])]
        return {'domain': {'sale_line_id': domain}}

    @api.depends('sale_line_id', 'sale_line_id.order_id.x_studio_block_timesheet_log',
                 'sale_line_id.x_studio_remaining_quantity', 'sale_line_id.x_studio_consumed_qty', 'partner_id',
                 'partner_id.x_studio_authorize_to_log_hours_with_late_invoice', 'partner_id.followup_status',
                 'partner_id.x_studio_authorize_late_amount', 'partner_id.total_overdue', 'project_id.on_hold_reason',
                 'partner_id.invoice_ids.payment_state', 'sale_line_id.state')
    def compute_task_color(self):
        """Computes the task color based on project status, overdue invoices, consumed hours, and authorization rules.
Determines whether the user can safely log hours or needs to stop or proceed with caution.
Assigns Red, Orange, or Green to indicate blocked, warning, or normal logging conditions.
"""
        today = date.today()
        company_ids = self.env['res.company'].sudo().search([])
        previous_parent_id = self.env['res.partner']
        followup_status = ''
        total_overdue = 0.0
        for rec in self.filtered(lambda task: task.partner_id and task.project_id.partner_id and
                                              task.project_id.partner_id.id not in
                                              company_ids.mapped('partner_id').ids):
            # If the consumed qty is greater than or equal to allocated qty it will indicate to red color as one should
            # not add more qty.
            # if rec.project_id.id == 539:
            if rec.project_id.partner_id.id in company_ids.mapped('partner_id').ids:
                rec.write({'color': 10, 'color_state': '', 'warning_msg': False})
                continue
            if rec.project_id.on_hold_reason:
                rec.write({'color': 1, 'color_state': 'red',
                           'warning_msg': 'You can not log hour as the project is on hold for reason : %s' %
                                          (dict(rec.project_id._fields['on_hold_reason'].selection).get(
                                              rec.project_id.on_hold_reason))})
                continue
            parent_id = rec.partner_id.mapped('parent_id') or rec.partner_id
            invoice_ids = parent_id.invoice_ids + parent_id.mapped('child_ids').invoice_ids
            not_paid_invoice_ids = invoice_ids.filtered(
                lambda move: move.state == 'posted' and move.move_type == 'out_invoice' and
                             move.payment_state in ['not_paid', 'partial'] and move.invoice_date_due != False and
                             move.company_id.id == rec.company_id.id)

            # Get the followup status and total overdue of the company of which the task is.
            if previous_parent_id.id != parent_id.id:
                previous_parent_id = parent_id
                followup_status, total_overdue = rec.get_followup_status(parent_id)

            #################################### RED Color ####################################################
            # If partner(customer)'s followup_status in ['in_need_of_action', 'with_overdue_invoices'] and not authorize
            # to log hours on
            # late invoice it will indicate to red color as one should not log.
            # Customer should not be an internal company
            color = rec.get_task_color(parent_id, rec)
            if rec.partner_id.id not in company_ids.mapped('partner_id').ids and \
                    followup_status in ['in_need_of_action', 'with_overdue_invoices']:
                if not parent_id.x_studio_authorize_to_log_hours_with_late_invoice:
                    if not_paid_invoice_ids and any(inv_due_date < today for inv_due_date in
                                                    not_paid_invoice_ids.mapped('invoice_date_due') if
                                                    inv_due_date) and color == 1:
                        rec.write({'color': 1, 'color_state': 'red',
                                   'warning_msg': 'The customer %s is in late with payment, you can not log hours. '
                                                  'Contact the Salesperson.' % _(parent_id.name)})
                        continue
                if color == 1:
                    if total_overdue > parent_id.x_studio_authorize_late_amount:
                        if any(inv_due_date < today for inv_due_date in
                               not_paid_invoice_ids.mapped('invoice_date_due') if inv_due_date):
                            rec.write({'color': 1, 'color_state': 'red',
                                       'warning_msg': 'This customer is in late with payment, you can not log hours. '
                                                      'The customer has $' + str(round(total_overdue, 2)) +
                                                      ' in late and only $' +
                                                      str(round(rec.partner_id.x_studio_authorize_late_amount, 2)) +
                                                      'is authorized. Contact the Salesperson.'})
                            continue

            if rec.sale_line_id.product_id.service_policy == 'ordered_prepaid' and \
                    rec.sale_line_id.product_id.x_studio_product_to_receive:
                if round(rec.sale_line_id.x_studio_consumed_qty, 2) >= round(rec.sale_line_id.x_studio_qty_in_hours, 2):
                    if round(rec.sale_line_id.x_studio_consumed_qty, 2) >= \
                            round(rec.sale_line_id.x_studio_qty_in_hours, 2):
                        rec.write({'color': 1, 'color_state': 'red',
                                   'warning_msg': 'You can not log hours on this project ' + rec.partner_id.name +
                                                  '. All the hours are consumed. Please contact the Salesperson.'})
                        continue
                    rec.write({'color': 1, 'color_state': 'red',
                               'warning_msg':
                                   'You can only log ' +
                                   str(rec.sale_line_id.x_studio_qty_in_hours - rec.sale_line_id.x_studio_consumed_qty)
                                   +
                                   'hours on this project. All the hours are consumed. '
                                   'Please contact the Salesperson about ' + rec.sale_line_id.order_id.name + '.'})
                    continue

            # If sale order is blocked any way task will have red indication
            if rec.sale_line_id.order_id.x_studio_block_timesheet_log:
                rec.write({'color': 1, 'color_state': '', 'color_state': 'red',
                           'warning_msg': 'Related Sale Order is blocked. Contact the Salesperson.'})
                continue

            ####################################### Orange Color #######################################################
            if rec.partner_id.id not in company_ids.mapped(
                    'partner_id').ids and not_paid_invoice_ids and today <= (
                    min(not_paid_invoice_ids.mapped('invoice_date_due')) + timedelta(
                days=rec.company_id.number_of_days_authorized_in_late)) and min(
                not_paid_invoice_ids.mapped('invoice_date_due')) < today:
                if ((parent_id.x_studio_authorize_to_log_hours_with_late_invoice and
                     parent_id.x_studio_authorize_late_amount < total_overdue) or
                        (rec.partner_id.x_studio_authorize_to_log_hours_with_late_invoice and
                         rec.partner_id.x_studio_authorize_late_amount < total_overdue) or
                        not parent_id.x_studio_authorize_to_log_hours_with_late_invoice):
                    rec.write({'color': 2, 'color_state': 'orange',
                               'warning_msg': 'Invoice is already due, be carreful, the project will be blocked soon. Ask the salesperson to talk with the customer ASAP!'})
                    continue

            # Time left on sale order line is less than 10 hours --> Color is Orange "Only 10 hour left to log the
            # timesheet, Ask customer to buy more hours!"
            if rec.sale_line_id and rec.sale_line_id.product_id.service_policy == 'ordered_prepaid' and \
                    (round(rec.sale_line_id.x_studio_remaining_quantity, 2)) < 10 and \
                    rec.sale_line_id.product_id.x_studio_product_to_receive:
                rec.write({'color': 2, 'color_state': 'orange',
                           'warning_msg': 'Only ' + ' ' +
                                          str(round(rec.sale_line_id.x_studio_remaining_quantity, 2)) +
                                          ' hour left to log the timesheet, Ask salesperson to sale more hours!'})
                continue

            # Invoice is due in less than 5 days --> Color is Orange
            # "Invoice is going to be due, ask customer to make payment!"
            day_left = today + timedelta(days=5)
            if rec.partner_id.id not in company_ids.mapped('partner_id').ids:
                if not_paid_invoice_ids and any(date_due < day_left for date_due in
                                                not_paid_invoice_ids.mapped('invoice_date_due')):
                    rec.write({'color': 2, 'color_state': 'orange',
                               'warning_msg': 'Invoice is going to be due, Remind customer to make payment!'})
                    continue

            ######################################## Green Color #######################################################
            rec.write({'color': 10, 'color_state': '', 'warning_msg': False})

    def preview_task_portal_custom(self):
        """
        for Portal view
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }

    # def send_webhook(self, url, headers, data):
    #     """From ksc_microsoft_team_connector"""
    #     response = requests.post(url, data=json.dumps(data), headers=headers)
    #     return True
