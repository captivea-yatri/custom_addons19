# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
import logging
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import ValidationError
from datetime import date

_logger = logging.getLogger(__name__)


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_type = fields.Selection(
        [('sale', 'Sale: Revenue Recognition'), ('purchase', 'Purchase: Asset'), ('expense', 'Deferred Expense')],
        compute='_compute_asset_type', store=True, index=True, copy=True)
    is_reconciled = fields.Boolean('Is Reconciled', readonly=True)
    reconciliation_status = fields.Selection([('NA', 'NA'), ('To do', 'To do'), ('Done', 'Done'),
                                              ('waiting', 'Waiting to close')], store=True,
                                             string='Reconciliation Status',
                                             compute='_compute_revenue_expense_reconcile')
    account_depreciation_id = fields.Many2one(
        comodel_name='account.account',
        string='Depreciation Account',
        domain="[]",
        help="Account used in the depreciation entries, to decrease the asset value."
    )
    account_depreciation_expense_id = fields.Many2one(
        comodel_name='account.account',
        string='Expense Account',
        domain="[]",
        help="Account used in the periodical entries, to record a part of the asset as expense.")

    @api.depends('original_move_line_ids')
    @api.depends_context('asset_type')
    def _compute_asset_type(self):
        ''' Compute the asset type based on context or original move lines.'''
        for record in self:
            if not record.asset_type and 'asset_type' in self.env.context:
                record.asset_type = self.env.context['asset_type']
            if not record.asset_type and record.original_move_line_ids:
                account = record.original_move_line_ids.account_id
                record.asset_type = account.asset_type

    @api.depends('is_reconciled', 'state', 'book_value', 'original_move_line_ids',
                 'original_move_line_ids.move_id', 'original_move_line_ids.move_id.payment_state')
    def _compute_revenue_expense_reconcile(self):
        """
        This function will compute the value of reconciliation status:
        Done: if is_reconciled field value is True,
        To Do: when revenue / expense has original_move_line_ids set + original_move_line_ids type is invoice or bill +
        and asset state is close + is_reconciled is false
        waiting : when revenue / expense has original_move_line_ids set + original_move_line_ids type is invoice or bill
        + and asset state is not close + is_reconciled is false
        NA : Else NA (Which means that is_reconciled is false + original_move_line_ids is not set or
        original_move_line_ids type is not invoice / bill or asset state is draft).
        """
        for rec in self:
            if rec.is_reconciled == True:
                rec.reconciliation_status = 'Done'
            elif rec.is_reconciled == False and rec.state == 'close' and rec.original_move_line_ids and \
                    rec.original_move_line_ids.mapped('move_id').filtered(
                        lambda move: move.move_type in ('in_invoice', 'out_invoice')):
                rec.reconciliation_status = 'To do'
            elif rec.is_reconciled == False and rec.state != 'close' and rec.original_move_line_ids and \
                    rec.original_move_line_ids.mapped('move_id').filtered(
                        lambda move: move.move_type in ('in_invoice', 'out_invoice')):
                rec.reconciliation_status = 'waiting'
            else:
                rec.reconciliation_status = 'NA'

    @api.model_create_multi
    def create(self, vals_list):
        ''' Compute value method called during the creation of account assets to calculate original value.'''
        # override create method to calculate original value.
        res = super(AccountAsset, self).create(vals_list)
        res._compute_value()
        return res

    def auto_reconcile_deferred_revenue_expense(self):
        """
        This function reconciles the revenue lines of deferred revenue and deferred expense with related invoice and
        related bill.
        """
        move_ids = self.env['account.move'].search(
            [('line_ids.asset_ids', '=', self.id), ('move_type', '=', 'in_invoice') if self.asset_type == 'expense'
             else ('move_type', '=', 'out_invoice')])
        if move_ids:
            move_ids_with_dr_de = self.filtered(lambda recc: recc.account_asset_id.id == self.account_depreciation_id.id
                                                             or recc.account_asset_id.id ==
                                                             self.account_depreciation_expense_id.id)
            if move_ids_with_dr_de:
                invoice_bill_line = move_ids.line_ids.filtered(lambda rec: rec.account_id.id ==
                                                                                   self.account_asset_id.id)
                if invoice_bill_line:
                    revenue_line_ids = self.env['account.move'].search(
                        [('asset_id', '=', self.id), ('move_type', '=', 'entry')])
                    move_line = revenue_line_ids.line_ids.filtered(
                        lambda record: record.account_id.id == self.account_asset_id.id)
                    if move_line:
                        (invoice_bill_line + move_line).filtered_domain([('reconciled', '=', False)]).reconcile()
                        self.write({'is_reconciled': True})
                    else:
                        raise ValidationError('Revenue line not found with the same type of account!')
                else:
                    raise ValidationError(
                        'Bill not found with the same type of account!') if self.asset_type == 'expense' else \
                        ValidationError('Invoice not found with the same type of account!')
            else:
                raise ValidationError('Bill Account Mismatched') if self.asset_type == 'expense' else \
                    ValidationError('Invoice Account Mismatched')
        else:
            raise ValidationError('Bill not found!') if self.asset_type == 'expense' else \
                ValidationError("Invoice not found!")

    def automatically_reconcile_deferred_revenue_expense(self):
        """
        This function reconciles the revenue line of deferred revenue and deferred expense with related invoice and bill
        automatic when deferred revenue and deferred expense is close state. This will work were only when the revenue
        is not created automatically which means this will work only for default odoo's account assets.
        """
        company_ids = self.company_id.browse([1, 3, 9, 10, 12])
        account_asset_ids = self.search(['|', ('asset_type', '=', 'sale'), ('asset_type', '=', 'expense'),
                                         ('state', '=', 'close'),
                                         ('is_reconciled', '=', False), ('company_id', 'in', company_ids.ids)])
        for account_asset_id in account_asset_ids:
            move_ids = self.env['account.move'].search(
                [('line_ids.asset_ids', '=', account_asset_id.id),
                 ('move_type', '=', 'in_invoice') if account_asset_id.asset_type == 'expense'
                 else ('move_type', '=', 'out_invoice')])
            if move_ids:
                move_ids_with_dr_de = account_asset_id.filtered(lambda recc: recc.account_asset_id.id ==
                                                                 account_asset_id.account_depreciation_id.id or
                                                                 recc.account_asset_id.id ==
                                                                 account_asset_id.account_depreciation_expense_id.id)
                if move_ids_with_dr_de:
                    invoice_bill_line = move_ids.line_ids.filtered(lambda rec: rec.account_id.id ==
                                                                               account_asset_id.account_asset_id.id)
                    if invoice_bill_line:
                        revenue_line_ids = self.env['account.move'].search(
                            [('asset_id', '=', account_asset_id.id), ('move_type', '=', 'entry')])
                        move_line = revenue_line_ids.line_ids.filtered(lambda record: record.account_id.id ==
                                                                                      account_asset_id.account_asset_id.id)
                        if move_line:
                            account_asset_id.auto_reconcile_deferred_revenue_expense()
                        else:
                            _logger.info(
                                "REVENUE LINE NOT FOUND WITH THE SAME TYPE OF ACCOUNT OF %r",
                                account_asset_id)
                    else:
                        _logger.info("BILL OR INVOICE NOT FOUND WITH THE SAME TYPE OF ACCOUNT OF %r",
                                     account_asset_id)
                else:
                    _logger.info("Bill or Invoice Account Mismatched of %r", account_asset_id)
            else:
                _logger.info("BILL OR INVOICE IS NOT FOUND OF %r", account_asset_id)
