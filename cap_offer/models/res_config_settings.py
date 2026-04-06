from odoo import fields, models, api,_


class ResCompany(models.Model):
    _inherit = "res.company"

    allow_offer_date = fields.Date(string="Offer Behavior Implementation Date")


class ResConfSetting(models.TransientModel):
    _inherit = "res.config.settings"

    allow_offer_date = fields.Date(string="Offer Behavior Implementation Date", related='company_id.allow_offer_date',
                                   readonly=False, store=True)

    def write(self, vals):
        res = super(ResConfSetting,self).write(vals)
        if 'allow_offer_date' in vals:
            self.env.company.write({'allow_offer_date':vals.get('allow_offer_date')})
        return res
