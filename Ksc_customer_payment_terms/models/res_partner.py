from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # is_default_after_first_payment = fields.Boolean(string="Default After First Payment")

    @api.model
    def default_get(self, fields_list):
        """
        This method is used to set default payment into customer payment term
        """
        default = super(ResPartner, self).default_get(fields_list)
        domain = [('company_id', '=', False), ('is_default', '=', True)]
        if self.env.company and not self.company_id:
            domain = [('company_id', '=', self.env.company.id), ('is_default', '=', True)]
        if self.company_id:
            domain = [('company_id', '=', self.company_id.id), ('is_default', '=', True)]
        payment_term = self.env['account.payment.term'].search(domain, limit=1)
        default['property_payment_term_id'] = payment_term and payment_term.id or False
        return default
