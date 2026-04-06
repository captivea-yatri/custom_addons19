# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import ast
from odoo.tools import date_utils


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.constrains('employee_id', 'unit_amount', 'so_line', 'date')
    def check_employee_restriction(self):
        """
        Based on employee filter configure on related sale order line employee can add timesheet else system will
        restrict other user.
        Pass validation when hours spent is greater than sale quota
        """
        for rec in self:
            if rec.so_line and rec.so_line.emp_filter_domain:
                domain = ast.literal_eval(rec.so_line.emp_filter_domain)
                restricted_empl_ids = self.env['hr.employee'].sudo().search(domain)
                if rec.employee_id.active and rec.employee_id not in restricted_empl_ids and rec.employee_id.user_id.override_filter != True:
                    raise ValidationError(
                        '%s is restricted to log time for selected sale order line due to there are filters on the sale order line, contact the salesperson.' %
                        (rec.employee_id.name))
            rec.check_employee_hrs_qty()

    def check_employee_hrs_qty(self):
        ''' Method is used to check if Employee hours logged in timesheet does not exceed the quota defined'''
        if self.so_line and self.so_line.so_line_quota_ids:
            start_date = date_utils.start_of(self.date, 'month')
            end_date = date_utils.end_of(start_date, 'month')
            line_quota_id = self.so_line.so_line_quota_ids.filtered(lambda line_quota:
                                                                   line_quota.employee_id.id == self.employee_id.id)
            if line_quota_id:
                employee_timesheet_ids = self.so_line.mapped('timesheet_ids').filtered(
                    (lambda timesheet: timesheet.employee_id == self.employee_id and
                                                          timesheet.date >= start_date and
                                                          timesheet.date <= end_date))
                total_added_timesheet = sum(employee_timesheet_ids.mapped('unit_amount'))
                if total_added_timesheet > line_quota_id.hrs_qty:
                    raise ValidationError(f'You cannot log more than {line_quota_id.hrs_qty} hours in a month!')
