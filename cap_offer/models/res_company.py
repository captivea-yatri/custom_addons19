from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.company'

    offer_ids = fields.One2many('company.offer.line', 'company_id', string='Offer')
    use_offer = fields.Boolean(string='Use Offer')

    @api.constrains('offer_ids')
    def _check_duplicate_product(self):
        for rec in self:
            offer_ids = []
            for offer in rec.offer_ids:
                if offer.offer_id and offer.offer_id.id in offer_ids:
                    raise ValidationError(f"You cannot use the same Offer - {offer.offer_id.name} more than once.")
                offer_ids.append(offer.offer_id.id)


class CompanyOfferLine(models.Model):
    _name = "company.offer.line"
    _description = "Company - Offer - User Link"

    company_id = fields.Many2one('res.company', string="Company")
    offer_ids = fields.Many2one('offer.offer', string="Offer")
    user_id = fields.Many2one('res.users', string="User")

