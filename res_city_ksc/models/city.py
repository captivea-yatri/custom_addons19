from odoo import models, fields

class City(models.Model):
    _name = "city"
    _description = "city"

    name = fields.Char(string="Name of the city", required=True)
    sh_name = fields.Char(string="Short Code of the city", required=True)
    active = fields.Boolean(string="Active", required=True)

