from odoo import fields, models, api

class ActionTemplateSubstitute(models.Model):
    _name = 'action.template.substitute'
    _description = 'Action Template Substitute'
    
    user_id = fields.Many2one('res.users', string='User')
    template_id = fields.Many2one('action.template', string='Template')
    sequence = fields.Integer(string='Sequence', help="Used to order. Lower is better.")

