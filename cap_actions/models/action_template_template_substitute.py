from odoo import fields, models, api
from datetime import date, timedelta

import random

class ActionTemplateTemplateSubstitute(models.Model):
    _name = 'action.template.template.substitute'
    _description = 'Action Template Template Substitute'
    
    user_id = fields.Many2one('res.users', string='User')
    template_template_id = fields.Many2one('action.template.template', string='Template')
    sequence = fields.Integer(string='Sequence', help="Used to order. Lower is better.")