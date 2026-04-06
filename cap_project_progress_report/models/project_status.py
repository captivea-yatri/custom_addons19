from odoo import models, fields, api


class ProjectStatus(models.Model):
    _inherit = 'project.status'

    project_progress_template = fields.Selection(
        [('project_progress_with_deadline', 'Project Progress Report with Deadline'),
         ('project_progress_no_deadline', 'Project Progress Report No Deadline')], string='Project Progress Template')