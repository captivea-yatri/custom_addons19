from odoo import fields, models, api
from datetime import date, timedelta

import random

class ActionTemplateTemplateValidation(models.Model):
    _name = 'action.template.template.validation'
    _description = 'Action Template Template Validation'
    
    template_template_id = fields.Many2one('action.template.template', string='Template')
    user_id = fields.Many2one('res.users', string='Validator')
    sequence = fields.Integer(string='Sequence', help="Used to order. Lower is better.")
    
    start = fields.Integer(string='Start',  default=100)
    ok_impact = fields.Float(string='OK Impact',  default=1)
    ko_impact = fields.Float(string='KO Impact',  default=1)
    max = fields.Integer(string='Max',  default=100)
    min = fields.Integer(string='Min',  default=0)