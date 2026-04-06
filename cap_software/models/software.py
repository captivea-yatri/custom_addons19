from odoo import fields, models, api


class Software(models.Model):
    _name = 'software.software'
    _description = 'Software Information'

    name = fields.Char(string='Name')
