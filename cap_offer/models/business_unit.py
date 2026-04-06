from odoo import fields, models, api,_

class BusinessUnit(models.Model):
    _name = 'business.unit'

    name = fields.Char('Name')