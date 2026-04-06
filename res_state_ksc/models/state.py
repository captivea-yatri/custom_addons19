from odoo import models, fields

class State(models.Model):
    _name = "state"
    _description = "state"

    name = fields.Char(string="Name of the state", required=True)
    sh_name = fields.Char(string="Short Code of the state ", required=True)
    active = fields.Boolean(string="Active", required=True)