from odoo import models, fields

class ResCountryKsc(models.Model):
    _name = 'res.country.ksc'
    _description = 'Country'

    name = fields.Char(required=True)
    country_code = fields.Char(required=True, string='Country Code')

    _sql_constraints = [
        ('unique_country_code', 'unique(country_code)', 'Country code must be unique!')
    ]
