# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    related_project_id = fields.Integer(string='Related Project Id')
