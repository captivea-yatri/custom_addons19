# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    limitation_of_skill_request = fields.Integer(string="Limitation Of Skill Request", readonly=False,
                                                 related='company_id.limitation_of_skill_request')

