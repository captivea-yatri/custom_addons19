from odoo import fields, models, api
from datetime import date, timedelta

import random

class ActionTemplateTemplate(models.Model):
    _name = 'action.template.template'
    _description = 'Action Template Template'
    
    name = fields.Char(string='Name')
    
    validation_ids = fields.One2many('action.template.template.validation', 'template_template_id', string="Validations")
    substitute_ids = fields.One2many('action.template.template.substitute', 'template_template_id', string="Substitutes")
    