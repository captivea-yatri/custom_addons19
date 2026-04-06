# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class InternalProjectQuotas(models.Model):
    _name = "internal.project.quotas"
    _description = 'Internal Project Quotas'

    name = fields.Char(string='name')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    hours_per_month = fields.Integer(string='Hours per Month')
    project_id = fields.Many2one('project.project', string='Project')

    @api.constrains('project_id', 'employee_id')
    def unique_employee_project_quota_constraint(self):
        """Ensures that each employee has only one quota entry per project.
When saving a record, it checks for existing internal.project.quotas with the same
employee and project combination (excluding the current record).
Raises a ValidationError if a duplicate quota is found."""
        for rec in self:
            quota = self.search([('id', '!=', rec.id), ('project_id', '=', rec.project_id.id),
                                 ('employee_id', '=', rec.employee_id.id)])
            if quota:
                raise ValidationError(
                    "Employee '{}' is already Exists for Project '{}' in Internal Project Quota".format(
                        rec.employee_id.name, rec.project_id.name))
