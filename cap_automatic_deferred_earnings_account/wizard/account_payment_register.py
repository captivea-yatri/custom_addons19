# Part of CAPTIVEA. Odoo  E.

from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    description = fields.Text(string="Please Provide details here ")

    def _create_payments(self):
        ''' Set the description on the payment created from the wizard '''
        context = dict(self._context)
        context.setdefault('default_description', self.description)
        self = self.with_context(context)
        return super(AccountPaymentRegister, self)._create_payments()
