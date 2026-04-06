# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
# from odoo.addons.sale_timesheet_enterprise.models.sale import DEFAULT_INVOICED_TIMESHEET
from odoo.addons.sale_timesheet_enterprise.models.sale_order_line import DEFAULT_INVOICED_TIMESHEET
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    task_color = fields.Integer(string="Task Color", related='task_id.color')
    task_warning_msg = fields.Char(string="Task Warning Message", related='task_id.warning_msg')
    extra_timesheet = fields.Boolean('Extra')
    restrict_manual_timesheet = fields.Boolean(related='project_id.restrict_manual_timesheet')

    @api.depends('task_id')
    def _compute_so_line(self):
        """For each timesheet record that does not already have `so_line` set,
    it assigns the Sale Order Line linked to the task on the timesheet."""
        for timesheet in self.filtered(lambda tm: not tm.so_line):
            timesheet.so_line = timesheet.task_id.sale_line_id

    @api.onchange('task_id')
    def change_task(self):
        """ This onchange method is triggered whenever the user adds a new timesheet line i will set the unit_amount: 0.0."""
        for rec in self:
            rec.unit_amount = 0.0

    def _timesheet_get_portal_domain(self):
        """
        Used to remove validated domain when user has portal_view_all_timesheet = true.
        """
        domain = super(AccountAnalyticLine, self)._timesheet_get_portal_domain()
        param_invoiced_timesheet = self.env['ir.config_parameter'].sudo().get_param('sale.invoiced_timesheet',
                                                                                    DEFAULT_INVOICED_TIMESHEET)
        if param_invoiced_timesheet == 'approved' and self.env.user.portal_view_all_timesheet:
            current_index = 1
            for elem in domain:
                if type(elem) == tuple and elem[0] == 'validated':
                    break
                current_index += 1
            domain.pop(len(domain) - current_index)
            domain.pop(current_index - 2)
        return domain

    def write(self, vals):
        """
        Checks a timesheet entry if the entry is from the previous month or older it also checks the hours which
        are present in the timesheet and can't allow to reduce it.
        if user have special right user will be able to
        reduce the timesheet.
        You can not reduce the timesheet of "dead" project.
        """
        current_month = fields.Date.today() + relativedelta(day=1)
        half_of_month = current_month + relativedelta(days=15)
        previous_month = current_month + relativedelta(months=-1)
        for rec in self.filtered(lambda rec: rec.date):
            # Restrict Modification For Dead Project
            if rec.project_id.project_status_id.code == 'dead' and (
                    not self.env.context.get('timesheet_validation', False) and not self.env.context.get('by_for_timesheet',
                                                                                                   False)):
                raise ValidationError('You cannot modify timesheet for a project which is Dead!')
            # Check Authorized Invoicing Amount
            new_so_line = self.env['sale.order.line'].browse(vals.get('so_line')) if vals.get('so_line') else False
            if ((vals.get('unit_amount') or vals.get(
                    'so_line')) and rec.so_line.product_id.service_policy == 'delivered_timesheet' and rec.order_id.authorized_invoicing_amount > 0.00
                    or (vals.get(
                        'so_line') and new_so_line.product_id.service_policy == 'delivered_timesheet' and new_so_line.order_id.authorized_invoicing_amount > 0.00)):
                if vals.get(
                        'so_line') and rec.so_line.product_id.service_policy == 'delivered_timesheet' and new_so_line.product_id.service_policy != 'delivered_timesheet':
                    pass
                elif vals.get('unit_amount') and vals.get(
                        'so_line') and new_so_line.product_id.service_policy == 'delivered_timesheet':
                    if (round(rec.so_line.price_unit * rec.unit_amount - new_so_line.price_unit * vals.get(
                            'unit_amount'), 2) < 0 and (
                            abs(round(rec.so_line.price_unit * rec.unit_amount - new_so_line.price_unit * vals.get(
                                'unit_amount'),
                                      2)) + rec.order_id.not_invoiced_amount > rec.order_id.authorized_invoicing_amount)):
                        raise ValidationError(
                            'You Can not Log hours, Limit of Authorized Invoicing Amount is Exceeded')
                elif vals.get('so_line') and new_so_line.product_id.service_policy == 'delivered_timesheet':
                    if (round(rec.so_line.price_unit * rec.unit_amount - new_so_line.price_unit * rec.unit_amount,
                              2) < 0 and (
                            abs(round(
                                rec.so_line.price_unit * rec.unit_amount - new_so_line.price_unit * rec.unit_amount,
                                2)) + rec.order_id.not_invoiced_amount > rec.order_id.authorized_invoicing_amount)):
                        raise ValidationError(
                            'You Can not Log hours, Limit of Authorized Invoicing Amount is Exceeded')
                elif vals.get('unit_amount') and (round(rec.unit_amount - vals.get('unit_amount'), 2) < 0 and (
                        abs(round(rec.unit_amount - vals.get('unit_amount'),
                                  2)) * rec.so_line.price_unit + rec.order_id.not_invoiced_amount > rec.order_id.authorized_invoicing_amount)):
                    raise ValidationError(
                        'You Can not Log hours, Limit of Authorized Invoicing Amount is Exceeded')

            # Automated action : Check Timesheet Log Creation
            rec.check_timesheet_log_creation(vals)
            # For Past Month Timesheet
            existing_month_start_date = rec.date + relativedelta(day=1)
            existing_month_end_date = (existing_month_start_date + relativedelta(months=1)) + relativedelta(days=-1)
            if rec.date < current_month and rec.project_id and rec.task_id:
                if fields.Date.today() >= half_of_month:
                    if ((vals.get('unit_amount', False) and rec.unit_amount > vals.get('unit_amount')) or \
                        (vals.get('date', False) and (str(vals.get('date')) < str(existing_month_start_date) or \
                                                      str(vals.get('date')) > str(existing_month_end_date)))) and \
                            not rec.env.user.has_group('ksc_project_extended.group_reduce_past_timesheet'):
                        raise ValidationError('You can not reduce past month timesheet!')
                else:
                    if rec.date < previous_month:
                        if ((vals.get('unit_amount', False) and rec.unit_amount > vals.get('unit_amount')) or \
                            (vals.get('date', False) and (str(vals.get('date')) < str(existing_month_start_date) or \
                                                          str(vals.get('date')) > str(
                                        existing_month_end_date)))) and not \
                                rec.env.user.has_group('ksc_project_extended.group_reduce_past_timesheet'):
                            raise ValidationError('You can not reduce past month timesheet!')
        return super(AccountAnalyticLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """It blocks timesheet creation on dead projects unless explicitly allowed through context.
It prevents logging hours on delivered-timesheet services when the sale order’s authorized invoicing limit is exceeded.
After creating each record, it triggers check_timesheet_log_creation() to run additional automated validations."""
        res = super(AccountAnalyticLine, self).create(vals_list)
        for rec in res:
            # Restrict Timesheet Creation For Dead Project
            if rec.project_id.project_status_id.code == 'dead' and not self.env.context.get('timesheet_validation', False):
                raise ValidationError('You cannot log hours for a project which is Dead!')
            # Check Authorized Invoicing Amount
            elif rec.so_line.product_id.service_policy == 'delivered_timesheet' and rec.order_id.authorized_invoicing_amount > 0.00:
                if rec.order_id.not_invoiced_amount > rec.order_id.authorized_invoicing_amount:
                    raise ValidationError(
                        'You Can not Log hours, Limit of Authorized Invoicing Amount is Exceeded')
            rec.with_context(from_create=True).check_timesheet_log_creation(vals_list[0])
        return res

    def check_timesheet_log_creation(self, values):
        """Validates timesheet logging by enforcing multiple business rules, including
mandatory sale order line checks, blocked sale order restrictions, customer
payment follow-up status, and internal monthly quota limits. Also updates
consumed hours on the related sale order line after successful validation."""
        ID_PARTNER_CAPTIVEA_USA = 1
        ID_PARTNER_CAPTIVEA_FRANCE = 102
        ID_PARTNER_CAPTIVEA_LUX = 247789
        ID_PARTNER_CAPTIVEA_FRANCE_NORTH = 333056
        for record in self.filtered(lambda rec: rec.project_id):
            task = record.task_id
            so_line = record.so_line.sudo()
            if not so_line:
                so_line = task.sale_line_id
            if ((not so_line or values.get(
                    'so_line') == False) and record.project_id.allow_billable and record.project_id.billing_type != 'not_billable' and
                    record.date > fields.Date(fields.Date.today().year, 1, 1)):
                if not values.get('so_line') and not so_line and not self.env.context.get('by_for_timesheet', False):
                    raise UserError('You can not log hours if you don\'t have a sale order line defined debug:' + str(
                        record["id"]))

            so = so_line.order_id
            partner = self.env['res.partner'].sudo().browse(record.partner_id.id)
            project = record.project_id
            if not partner:
                partner = project.partner_id
            if partner.parent_id:
                partner = partner.parent_id
            if partner:
                employee = record.employee_id.sudo()
                if (values.get('unit_amount') and values.get('unit_amount') > 0.00) or values.get('so_line'):

                    # For Blocked sale order
                    if so.x_studio_block_timesheet_log == True and not self.env.context.get('by_for_timesheet', False):
                        raise UserError('This Sale Order is blocked(' + str(so.id) + '). Contact the Salesperson.')

                    if partner.id not in self.env['res.company'].sudo().search([]).mapped('partner_id').ids:
                        followup_status, total_overdue = task.get_followup_status(partner)
                        color = task.get_task_color(partner, task)
                        if followup_status in ['in_need_of_action', 'with_overdue_invoices'] and total_overdue:
                            if not self.env.context.get('timesheet_validation', False) and not self.env.context.get(
                                    'by_for_timesheet', False):
                                if partner.x_studio_authorize_to_log_hours_with_late_invoice == False and color == 1:
                                    raise UserError(
                                        'The customer ' + partner.name + ' is in late with payment, you can not log hours. Contact the Salesperson.')
                                if total_overdue > partner.x_studio_authorize_late_amount and color == 1:
                                    raise UserError(
                                        'This customer is in late with payment, you can not log hours. The customer has $' + str(
                                            round(
                                                total_overdue, 2)) + ' in late and only $' + str(round(
                                            partner.x_studio_authorize_late_amount,
                                            2)) + 'is authorized. Contact the Salesperson.')

                    # Verification Internal quota
                if ((
                        project.partner_id.id == ID_PARTNER_CAPTIVEA_USA or project.partner_id.id == ID_PARTNER_CAPTIVEA_FRANCE
                        or project.partner_id.id == ID_PARTNER_CAPTIVEA_LUX or project.partner_id.id == ID_PARTNER_CAPTIVEA_FRANCE_NORTH) and project.id != project.company_id.project_leave_id.id and not project.restrict_manual_timesheet):
                    consumed_project_hours = 0.0
                    first_day = fields.Date.today().replace(day=1)
                    next_month_first_day = (first_day + relativedelta(months=1))
                    # for aline in self.env['account.analytic.line'].search(
                    #         [('project_id', '=', project.id), ('employee_id', '=', employee.id),
                    #          ('date', '>=', fields.Date.today().strftime('%Y-%m-1')), ('date', '<', (
                    #                 fields.Date.today() + relativedelta(months=1)).strftime(  # dateutil.relativedelta.
                    #             '%Y-%m-1'))]):
                    for aline in self.env['account.analytic.line'].search([
                        ('project_id', '=', project.id),
                        ('employee_id', '=', employee.id),
                        ('date', '>=', first_day),
                        ('date', '<', next_month_first_day)
                    ]):
                        consumed_project_hours = consumed_project_hours + aline.unit_amount
                        quota = self.env['internal.project.quotas'].search(
                            [('employee_id', '=', employee.id), ('project_id', '=', project.id)])

                        if not quota and not self.env.context.get('by_for_timesheet', False):
                            raise UserError(
                                'You are not authorized to log hours on this project (not quota) debug:' + str(
                                    record.id))
                        elif consumed_project_hours > quota.hours_per_month and not self.env.context.get(
                                'by_for_timesheet', False):
                            left = quota.hours_per_month - consumed_project_hours
                            raise UserError('You are authorized to log ' + str(
                                quota.hours_per_month) + ' hours per month on this project. You have only ' + str(
                                left) + ' hours left')

                # update consumed_qty on so_line
                consumed_hours = 0.0
                for aline in self.env['account.analytic.line'].search([('so_line', '=', so_line.id), (
                        'project_id', 'not in', [539, 810])]):  # Exclude Developer Central hours
                    consumed_hours = consumed_hours + aline.unit_amount
                so_line.x_studio_consumed_qty = consumed_hours
                if values.get('so_line') and not self.env.context.get('from_create', False):
                    so_line.x_studio_consumed_qty = consumed_hours - record.unit_amount
                    new_so_line = self.env['sale.order.line'].browse(values.get('so_line')).sudo()
                    consumed_hours = 0.00
                    for aline in self.env['account.analytic.line'].search([('so_line', '=', new_so_line.id), (
                            'project_id', 'not in', [539, 810])]):
                        consumed_hours = consumed_hours + aline.unit_amount
                    new_so_line.x_studio_consumed_qty = consumed_hours + record.unit_amount

    def unlink(self):
        """
        Checks a timesheet entry if the entry is from the previous month or older then it can't allow to delete it.
        if user have special right user will be able to delete the timesheet.
        """
        current_month = fields.Date.today() + relativedelta(day=1)
        for rec in self.filtered(lambda rec: rec.date):
            if rec.project_id.project_status_id.code == 'dead':
                raise ValidationError('You cannot delete timesheet for a project which is Dead!')
            elif rec.project_id.restrict_manual_timesheet and not self.env.context.get('from_inter_company', False):
                raise UserError('You cannot delete timesheet for a project on which Restrict Manual Timesheet is True')
            elif rec.date < current_month and rec.project_id and rec.task_id:
                if fields.Date.today() >= current_month + relativedelta(days=15) and not rec.env.user.has_group(
                        'ksc_project_extended.group_reduce_past_timesheet') and rec.id not in self.env[
                    'hr.leave'].search([]).filtered(lambda rec: rec.timesheet_ids).timesheet_ids.ids:
                    raise ValidationError('You can not delete past month timesheet!')
                else:
                    if rec.date < current_month + relativedelta(months=-1) and not rec.env.user.has_group(
                            'ksc_project_extended.group_reduce_past_timesheet') and rec.id not in self.env[
                        'hr.leave'].search([]).filtered(lambda rec: rec.timesheet_ids).timesheet_ids.ids:
                        raise ValidationError('You can not delete past month timesheet!')
        return super(AccountAnalyticLine, self).unlink()

    @api.constrains('project_id', 'unit_amount', 'date', 'employee_id')
    def _constrains_timesheet(self):
        """Prevents creating or modifying timesheets on projects that are on hold due to
'waiting_customer' or 'conflict'."""
        for record in self:
            if record.project_id.on_hold_reason in ['waiting_customer', 'conflict'] and (
                    not self.env.context.get('timesheet_validation', False) and not self.env.context.get('by_for_timesheet',
                                                                                                   False)):
                raise UserError(
                    _('You cannot create or modify timesheet for project which has On Hold Reason with '
                      'Waiting Customer or Conflict'))
