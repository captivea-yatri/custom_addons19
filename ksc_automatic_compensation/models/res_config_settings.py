from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    compensate_account_payable_id = fields.Many2one(
        'account.account', related='company_id.compensate_account_payable_id', readonly=False,
        domain="[('account_type', '=', 'liability_payable')]",
        string='Account Payable')

    compensate_account_receivable_id = fields.Many2one(
        'account.account', related='company_id.compensate_account_receivable_id', readonly=False,
        domain="[('account_type', '=', 'asset_receivable')]",
        string='Account Receivable')

    compensate_journal_id = fields.Many2one(
        'account.journal', related='company_id.compensate_journal_id', readonly=False,
        string='Journal')

