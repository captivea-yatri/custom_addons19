# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    team_manager_project_id = fields.Many2one('project.project', 'Team Manager Project',
                                              domain="[('company_id', '=', id)]")
    project_leave_id = fields.Many2one('project.project', 'Project Leave Id',
                                       domain="[('company_id', '=', id)]")
    number_of_days_authorized_to_backlog_timesheet = fields.Integer('Number of days authorized to Backlog Timesheet')

    @api.constrains('number_of_days_authorized_to_backlog_timesheet')
    def _check_number_of_days_authorized_to_backlog_timesheet(self):
        """Validates that the number of days authorized for backlogging timesheets is not negative."""
        if self.number_of_days_authorized_to_backlog_timesheet < 0:
            raise ValidationError(_('Number of days authorized to backlog timesheet must be positive number!!!'))
