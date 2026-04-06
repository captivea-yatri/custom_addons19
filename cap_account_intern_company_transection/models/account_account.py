from odoo import api, fields, models, _, Command

class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.model
    def _get_most_frequent_account_for_partner(self, company_id, partner_id=False, move_type=False):
        """
            Overrides to skip automatic account suggestion during
            inter-company transactions to avoid cross-company mismatches.
        """

        if self.env.context and self.env.context.get('from_inter_company_transaction', False):
            return False
        else:
            return super(AccountAccount, self)._get_most_frequent_account_for_partner(
                company_id=company_id,
                partner_id=partner_id,
                move_type=move_type,

            )