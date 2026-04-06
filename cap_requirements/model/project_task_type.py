# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    is_done_for_captivea = fields.Boolean("Is Done for Captivea", default=False)