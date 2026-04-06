from odoo import models, fields, _, api


class ProjectFeedback(models.Model):
    _inherit = 'project.feedback'

    task_validation_status_id = fields.Many2one(comodel_name='task.validation.status', string='Task Validation Status')
