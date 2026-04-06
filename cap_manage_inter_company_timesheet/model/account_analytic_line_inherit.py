# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountAnalyticLineInherit(models.Model):
    _inherit = 'account.analytic.line'

    inter_company_timesheet_id = fields.Many2one('account.analytic.line', string='Inter Company Timesheet')

    @api.model_create_multi
    def create(self, vals):
        """
               Creates timesheet records and triggers intercompany project synchronization
               for entries not belonging to company ID 10 by calling check_internal_project().
        """
        res = super(AccountAnalyticLineInherit, self).create(vals)
        # company != Konsultoo USA
        for rec in res:
            if rec.employee_id and rec.project_id and rec.project_id.company_id.id != 10:
                rec.check_internal_project()
        return res

    def write(self, vals):
        """
              Updates timesheet records and maintains intercompany synchronization.
              If key fields are modified, it removes outdated intercompany entries
              and revalidates intercompany timesheet linkage via check_internal_project().
        """
        res = super(AccountAnalyticLineInherit, self).write(vals)
        if set(vals.keys()) & set(['date', 'employee_id', 'name', 'unit_amount', 'task_id']):
            for rec in self.filtered(lambda t: t.project_id.company_id.id != 10):
                if rec.project_id.company_id.id == rec.employee_id.company_id.id or vals.get('employee_id', False):
                    timesheet_value = self.search([('inter_company_timesheet_id', '=', rec.id)])
                    if timesheet_value:
                        timesheet_value.with_context(from_inter_company=True).unlink()
                rec.check_internal_project()
        return res

    def check_internal_project(self):
        """
              Handles intercompany timesheet synchronization by ensuring:
              - Internal project exists between employee and project companies.
              - Creates intercompany task if missing.
              - Syncs or creates corresponding timesheet entry in the linked company.
              Raises validation errors for missing access or configuration.
         """
        for rec in self:
            employee_company = rec.employee_id.sudo().company_id
            project_company = rec.project_id.sudo().company_id
            if employee_company != project_company:
                project_id = self.env['project.project'].search([
                    ('partner_id', '=', project_company.partner_id.id),
                    ('project_status_id.code', '=', 'internal'),
                    ('company_id', '=', employee_company.id),
                ], limit=1)

                project_sudo = self.env['project.project'].sudo().search([
                    ('partner_id', '=', project_company.partner_id.id),
                    ('project_status_id.code', '=', 'internal'),
                    ('company_id', '=', employee_company.id),
                ], limit=1)

                if project_sudo and not project_id:
                    raise ValidationError(
                        f'You are unable to log a timesheet due to insufficient access to the contact {project_sudo.partner_id.name}. \nKindly create an access request for {project_sudo.partner_id.name}.')
                elif not project_sudo:
                    raise ValidationError(
                        'Timesheet logging is not possible due to a missing intercompany configuration. \nPlease contact to the CEO for further guidance.')
                project_task_id = self.env['project.task'].search([
                    ('related_project_id', '=', rec.project_id.id),
                    ('company_id', '=', employee_company.id),
                    ('partner_id', '=', project_company.partner_id.id),
                    ('project_id', '=', project_id.id)
                ])
                if not project_task_id:
                    # TODO : need to check for allocated hours and analytic account
                    project_task_id = self.env['project.task'].sudo().create({
                        'related_project_id': rec.project_id.id,
                        'name': rec.project_id.name,
                        'allocated_hours': rec.task_id.allocated_hours,
                        # 'analytic_account_id': project_id.sudo().analytic_account_id.id,
                        'company_id': employee_company.id,
                        'project_id': project_id.sudo().id,
                    })
                existing_timesheet = self.env['account.analytic.line'].search([
                        ('task_id', '=', project_task_id.id),
                        ('inter_company_timesheet_id', '=', rec.id)])
                if existing_timesheet:
                    existing_timesheet.sudo().write(
                        {'date': rec.date, 'employee_id': rec.employee_id.id,
                         'name': rec.name, 'unit_amount': rec.unit_amount})
                else:
                    self.env['account.analytic.line'].sudo().create({
                        'date': rec.date,
                        'employee_id': rec.employee_id.id,
                        'name': rec.name,
                        'unit_amount': rec.unit_amount,
                        # project_id.sudo().analytic_account_id.id
                        'account_id': project_id.sudo().account_id.id,
                        'task_id': project_task_id.id,
                        'company_id': employee_company.id,
                        'inter_company_timesheet_id': rec.id
                    })

    def unlink(self):
        """
        Deletes the timesheet and its linked intercompany timesheet record.
        Prevents recursive deletion by using context flag.
        """
        for rec in self:
            inter_company_timesheet = self.search([('inter_company_timesheet_id', '=', rec.id)])
            if inter_company_timesheet:
                inter_company_timesheet.with_context(from_inter_company=True).unlink()
        return super(AccountAnalyticLineInherit, self).unlink()

