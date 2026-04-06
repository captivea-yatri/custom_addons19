from odoo import fields, models, api
from datetime import date, timedelta

class GroupeService(models.Model):
    _name = 'group.service'
    _description = 'Group Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name')
    
    department_id = fields.Many2one('hr.department', string='Department')
    invoicing = fields.Selection([
        ('onboarding', 'On boarding'),
        ('Fees', 'Fees'),
        ('OnDemand', 'OnDemand'),
    ], string='Invoicing')
    
    invoicing_ondemand_by = fields.Char(string='On demand Invoicing by')
    
    description = fields.Html(string='Description')
    description_price = fields.Html(string='Price Description')
    price = fields.Float(string='Price')
    
