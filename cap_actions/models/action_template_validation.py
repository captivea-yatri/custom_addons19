from odoo import fields, models, api
from datetime import date, timedelta

class ActionTemplateValidation(models.Model):
    _name = 'action.template.validation'
    _description = 'Action Template Validation'
    
    template_id = fields.Many2one('action.template', string='Template')
    user_id = fields.Many2one('res.users', string='Validator')
    sequence = fields.Integer(string='Sequence', help="Used to order. Lower is better.")
    
    probability = fields.Float(string='Probability',  default=100)
    
    template_template_validation_id = fields.Many2one('action.template.template.validation', string='Template Tempalte Validation')

