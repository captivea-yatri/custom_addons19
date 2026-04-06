from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    asset_type = fields.Selection(
        [('sale', 'Deferred Revenue'), ('expense', 'Deferred Expense'), ('purchase', 'Asset')],
        compute='_compute_can_create_asset')

    is_off_balance = fields.Boolean(compute='_compute_is_off_balance', default=False, store=True, readonly=True)

    @api.depends('account_type')
    def _compute_can_create_asset(self):
        ''' Determine the type of asset to be created based on the account type.'''
        res = super()._compute_can_create_asset()
        for record in self:
            account_type = record.account_type
            if account_type in ('asset_fixed', 'asset_non_current'):
                record.asset_type = 'purchase'
            elif account_type in ('liability_non_current', 'liability_current'):
                record.asset_type = 'sale'
            elif account_type in ('asset_prepayments', 'asset_current'):
                record.asset_type = 'expense'
            else:
                record.asset_type = False
        return res

    @api.depends('internal_group')
    def _compute_is_off_balance(self):
        ''' If Internal Group is 'off_balance', then set is_off_balance to True.'''
        for account in self:
            account.is_off_balance = account.internal_group == "off_balance"

    '''Jaykishan - Commented the below methods. Previously getting called from compute method _compute_can_create_asset to set asset tyoe.'''
    # def auto_generate_asset(self):
    #     return self.account_type in ('asset_fixed', 'asset_non_current')
    #
    # def auto_generate_deferred_revenue(self):
    #     return self.account_type in ('liability_non_current', 'liability_current')
    #
    # def auto_generate_deferred_expense(self):
    #     return self.account_type in ('asset_prepayments', 'asset_current')