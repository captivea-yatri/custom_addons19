from odoo import models, fields

class Country(models.Model):
    _name = "country"
    _description = "country"

    name = fields.Char(string="Name of the country", required=True)
    sh_name = fields.Char(string="Short Code of the country ", required=True)
    active = fields.Boolean(string="Active", required=True)

