from odoo import api, fields, models


class ProjectStatus(models.Model):
    _name = 'project.status'
    _description = 'Project Status'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')


