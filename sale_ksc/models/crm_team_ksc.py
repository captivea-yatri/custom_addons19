from odoo import models, fields, api

class CrmTeamKSC(models.Model):
    _name = 'crm.team.ksc'
    _description = 'KSC Sales Team'

    name = fields.Char(string="Team Name", required=True)
    leader_name = fields.Many2one('res.users', string="Team Leader")
