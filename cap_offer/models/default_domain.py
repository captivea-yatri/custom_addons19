from odoo import fields, models, api,_


class DefaultDomain(models.Model):
    _inherit = 'default.domain'

    offer_ids = fields.Many2many('offer.offer', string='Offer')