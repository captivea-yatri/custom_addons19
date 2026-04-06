from odoo import models, api, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    software_id = fields.Many2one('software.software', string='Software')
