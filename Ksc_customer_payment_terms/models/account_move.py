from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = "account.move"


    def _compute_payment_state(self):
        """
        This method is used to set default after payment term in contacts payment term
        """
        rec = super(AccountMove, self)._compute_payment_state()
        for account_move_id in self:
            if account_move_id._origin:
                domain = [('partner_id', '=', account_move_id.partner_id.id), ('payment_state', '=', 'paid'),
                          ('id', '!=', account_move_id._origin.id)]
                if self.env.company and not account_move_id.company_id:
                    domain.append(('company_id', '=', self.env.company.id))
                elif account_move_id.company_id:
                    domain.append(('company_id', '=', account_move_id.company_id.id))
                else:
                    domain.append(('company_id', '=', False))
                partner_id = self.env['account.move'].search(domain)
                if account_move_id.payment_state == 'paid' and not partner_id:
                    domain = [('is_default_after_first_payment', '=', True)]
                    if self.env.company and not account_move_id.company_id:
                        domain.append(('company_id', '=', self.env.company.id))
                    elif account_move_id.company_id:
                        domain.append(('company_id', '=', account_move_id.company_id.id))
                    else:
                        domain.append(('company_id', '=', False))
                    default_after_first_payment = self.env['account.payment.term'].sudo().search(domain, limit=1)
                    if default_after_first_payment:
                        account_move_id.partner_id.write(
                            {'property_payment_term_id': default_after_first_payment.id})
        return rec
