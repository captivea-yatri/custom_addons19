from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """
        This method is used to auto register payment while confirm vendor bill or invoices
        """
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.move_type == 'out_invoice' or rec.move_type == 'in_invoice':
                auto_internal_transaction_configuration = rec.env['auto.internal.transaction.configuration'].search(
                    [('partner_id', '=', rec.partner_id.id), ('company_id', '=', rec.company_id.id)])
                if auto_internal_transaction_configuration:
                    payment_lines = auto_internal_transaction_configuration.journal_id.inbound_payment_method_line_ids \
                        if rec.move_type == 'in_invoice' \
                        else auto_internal_transaction_configuration.journal_id.outbound_payment_method_line_ids
                    if rec.amount_total > 0.0:
                        payment_register = self.env['account.payment.register'].with_context(active_ids=rec.ids,
                                                                         active_model='account.move'). \
                            create({'payment_type': 'inbound',
                                    'payment_method_line_id': payment_lines[:1].id,
                                    'partner_type': 'customer',
                                    'partner_id': rec.partner_id.id,
                                    'amount': rec.amount_total,
                                    'journal_id': auto_internal_transaction_configuration.journal_id.id,
                                    'payment_date': rec.invoice_date,
                                    })
                        # update context for auto_invoice_move_id 
                        payment = payment_register.with_context(auto_invoice_move_id=rec.id)._create_payments()
                        payment.action_validate()
        return res

    def button_draft(self):
        """Reset related payments to draft or cancel when the invoice is set to draft."""
        res = super(AccountMove, self).button_draft()
        payments = self.env['account.payment'].search([('auto_invoice_move_id', 'in', self.ids),
                                                       ('state', 'in', ['in_process','paid'])])
        for payment in payments:
            payment.action_draft()
            payment.action_cancel()
        return res

