# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_validate = fields.Boolean("Is Validated")
    hold = fields.Boolean("On Hold")
    is_permanent_task = fields.Boolean("Is permanent task")
    stage = fields.Selection([('To valid by cust in staging', 'To Valid by Customer in Staging'),
                              ('To push in production', 'To push in production'),
                              ('To valid by cust in production', 'To Valid by Cust in Production')])

class TaskHistoryLog(models.Model):
    _name = 'task.history.log'
    _description = 'Task History Log'

    name = fields.Char("Task Name", related="task_id.name")
    project_id = fields.Many2one("project.project", string="Project", related="task_id.project_id")
    task_id = fields.Many2one("project.task", string="Task")
    related_task_id = fields.Integer(related="task_id.id")
    is_planned = fields.Boolean("Is Planned?")
    state = fields.Char("Status", related="task_id.stage_id.name",translate=True, store=True)
    progress_report_id = fields.Many2one("project.progress")
    phase_id = fields.Many2one("project.phase", related="progress_report_id.phase_id")
    default_domain_ids = fields.Many2many(related="task_id.default_domain_ids")
    domain = fields.Many2one(comodel_name='default.domain', related="task_id.default_domain_id", string='Domain', store=True)
    sequence = fields.Integer(string='Sequence')

    @api.constrains('progress_report_id', 'task_id')
    def unique_task_progress_report_constraint(self):
        for rec in self:
            task = self.search([('id', '!=', rec.id), ('progress_report_id', '=', rec.progress_report_id.id),
                                 ('task_id', '=', rec.task_id.id)])
            if task:
                raise ValidationError(
                    "Task '{}' is already Exists for Project Progress Report '{}' ".format(
                        rec.task_id.name, rec.progress_report_id.name))


