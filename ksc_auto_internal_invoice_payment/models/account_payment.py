from odoo import api, models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    auto_invoice_move_id = fields.Many2one('account.move')

    @api.model_create_multi
    def create(self, vals_list):
        """
        If get auto_invoice_move_id in context update the value for auto_invoice_move_id in payment
        Specially for Equity account automatic.
        """
        if self._context and 'auto_invoice_move_id' in self._context:
            vals_list[0].update({'auto_invoice_move_id': self._context.get('auto_invoice_move_id')})
        return super(AccountPayment, self).create(vals_list)