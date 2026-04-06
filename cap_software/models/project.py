from odoo import fields, models, api


class Project(models.Model):
    _inherit = 'project.project'

    software_version_id = fields.Many2one('software.version', string="Software Version")


