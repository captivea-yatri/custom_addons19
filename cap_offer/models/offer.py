from odoo import fields, models, api,_


class OfferOffer(models.Model):
    _name = 'offer.offer'
    _description = "Offer"

    name = fields.Char(string='Name')
    restrict_time = fields.Boolean(string='Restrict time')
    combined_offer_ids = fields.Many2many('offer.offer', 'offer_combined_rel', 'main_offer_id', 'combined_offer_id',
                                          string='Combined Offers')
    sequence = fields.Integer(string='Sequence')
    business_unit_ids = fields.Many2many('business.unit','rel_offer_business_unit','business_unit_id','offer_id',string="Business Units")
    business_localisation_ids = fields.Many2many('business.localisation','rel_offer_business_localisation','business_localisation_id','offer_id',string="Business Localisations")