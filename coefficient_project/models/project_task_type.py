# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_default = fields.Boolean(string="Default In Projects")
