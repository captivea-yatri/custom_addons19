from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    is_default = fields.Boolean(string="Default")
    is_default_after_first_payment = fields.Boolean(string="Default After First Payment")

    @api.constrains('is_default', 'company_id', 'active')
    def _change_is_default_status(self):
        """
        This method is used to add restriction based on is_default
        """
        for rec in self:
            if rec.is_default:
                default_payment_terms = self.search([('id', '!=', rec.id), ('is_default', '=', 'True'),
                                                     ('company_id', '=', rec.company_id.id), ('active', '=', True)],
                                                    limit=1)
                if default_payment_terms:
                    raise ValidationError(_("Payment Term: '{}' already set as default. \n"
                                            "If you want to set Payment Term: '{}' as default "
                                            "Remove that Payment Term: '{}' from default.".format(
                        default_payment_terms.name, rec.name, default_payment_terms.name)))

    @api.constrains('is_default_after_first_payment', 'company_id', 'active')
    def _change_is_default_after_first_payment(self):
        """
        This method is used to add restriction based on is_default_after_first_payment
        """
        for rec in self:
            if rec.is_default_after_first_payment:
                default_after_first_payment = self.search([('id', '!=', rec.id),
                                                           ('is_default_after_first_payment', '=', 'True'),
                                                           ('company_id', '=', rec.company_id.id),
                                                           ('active', '=', True)], limit=1)
                if default_after_first_payment:
                    raise ValidationError(_("Payment Term: '{}' already set as Default After First Payment. \n"
                                            "If you want to set Payment Term: '{}' as Default After First Payment "
                                            "Remove that Payment Term: '{}' from Default After First Payment.".format(
                    default_after_first_payment.name, rec.name, default_after_first_payment.name)))
