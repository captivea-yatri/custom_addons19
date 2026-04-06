# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command,_
from odoo.tools import float_compare
from odoo.exceptions import ValidationError,UserError
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    last_payment_date = fields.Date('Last Payment Date', compute='_compute_last_payment_date', store=True)

########################################### TIME CREDIT FIELDS START  ##################################################
    time_credit_depreciated_value = fields.Monetary(string="Cumulative Depreciation",
                                                    compute="_compute_depreciation_cumulative_value_time_credit")
    time_credit_remaining_value = fields.Monetary(string='Depreciable Value',
                                                  compute='_compute_depreciation_cumulative_value_time_credit')
    depreciation_value_time_credit = fields.Monetary(string="Depreciation",
                                                     compute="_compute_depreciation_value_time_credit",
                                                     inverse="_inverse_depreciation_value_time_credit", store=True)
    time_credit_id = fields.Many2one('time.credit', string='Time Credit', index=True, copy=False, ondelete="set null",
                                     domain="[('company_id', '=', company_id)]")

    currency_rate_on_invoice_confirmation = fields.Float('Currency Rate On Invoice Confirmation',digits=(12, 14),store=True, copy = False)
########################################### TIME CREDIT FIELDS END  ####################################################
    def partner_credit_time_sync(self):
        ''' Update the Credit Time Synchronization for related partners.'''
        for rec in self:
            list_of_partners = []
            if rec.partner_id and rec.partner_id not in list_of_partners:
                list_of_partners.append(rec.partner_id)
            for line in rec.line_ids:
                if line.partner_id and line.partner_id not in list_of_partners:
                    list_of_partners.append(line.partner_id)
            if len(list_of_partners)>0:
                for partner in list_of_partners:
                    partner.update_time_credit_synchronization_for_partner(partner)

    def action_post(self):
        ''' Set the Currency Rate On Invoice Confirmation or set 'Time Credit' from related Sale Order on invoice posting and Update the Credit Time Synchronization for related partners.'''
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.currency_rate_on_invoice_confirmation = self.env['res.currency']._get_conversion_rate(
                    rec.currency_id, rec.company_id.currency_id, rec.company_id,
                    rec.invoice_date if rec.invoice_date else datetime.today().date())
                if not rec.time_credit_id:
                    source_time_credit = self.env['time.credit'].sudo().search([('sale_order_id','=',rec.line_ids.sale_line_ids[0].order_id.id if rec.line_ids.sale_line_ids else False)])
                    if source_time_credit:
                        rec.sudo().write({'time_credit_id':source_time_credit[0].id})
            rec.partner_credit_time_sync()
        return res

    def write(self, vals):
        ''' Update the Currency Rate On Invoice Confirmation on invoice date change/update.'''
        res = super(AccountMove, self).write(vals)
        for rec in self:
            if vals.get('invoice_date'):
                if rec.move_type == 'out_invoice':
                    rec.currency_rate_on_invoice_confirmation = rec.env['res.currency']._get_conversion_rate(
                        rec.currency_id, rec.company_id.currency_id, rec.company_id,
                        rec.invoice_date if rec.invoice_date else datetime.today().date())
        return res

    def button_cancel(self):
        ''' On canceling the entry, Update the Credit Time Synchronization for related partners.'''
        res = super().button_cancel()
        for record in self:
            # if record.move_type == 'out_invoice' and record.time_credit_id:
            #     related_time_credits = self.env['time.credit'].search([('sale_order_id','=',record.time_credit_id.sale_order_id.id)])
            #     for time_credit in related_time_credits:
            #         if time_credit.state in ('close','open'):
            #             raise UserError(_('You cannot archive a record that is linked with time credit'))
            record.partner_credit_time_sync()
        return res

    def button_draft(self):
        ''' On resetting to draft the entry, Update the Credit Time Synchronization for related partners.'''
        res = super().button_draft()
        for record in self:
            # if record.move_type == 'out_invoice' and record.time_credit_id:
            #     related_time_credits = self.env['time.credit'].search([('sale_order_id','=',record.time_credit_id.sale_order_id.id)])
            #     for time_credit in related_time_credits:
            #         if time_credit.state in ('close','open'):
            #             raise UserError(_('You cannot reset to draft an entry related to a posted Time Credit'))
            record.partner_credit_time_sync()
        return res


    @api.depends('line_ids.balance')
    def _compute_depreciation_value_time_credit(self):
        for move in self:
            time_credit = move.time_credit_id or move.reversed_entry_id.time_credit_id  # reversed moves are created before being assigned to the asset
            time_credit_depreciation = 0
            if time_credit:
                account_internal_group = 'income'
                time_credit_depreciation = sum(move.line_ids.filtered(
                    lambda l: l.account_id.internal_group == account_internal_group or
                              l.account_id == time_credit.account_depreciation_expense_id).mapped('balance')) * (-1)
                """Special case of closing entry - only disposed assets of type 'purchase' should match this condition
                The condition on len(move.line_ids) is to avoid the case where there is only one depreciation move, and 
                it is not a disposal move
                The condition will be matched because a disposal move from a disposal move will always have more than 
                2 lines, unlike a normal depreciation move
                """
                if any(line.account_id == time_credit.account_time_credit_id
                        and float_compare(-line.balance, time_credit.original_value,
                                          precision_rounding=time_credit.currency_id.rounding) == 0
                        for line in move.line_ids) and len(move.line_ids) > 2:
                    time_credit_depreciation = (time_credit.original_value - time_credit.salvage_value - (
                                move.line_ids[1].debit if time_credit.original_value > 0 else move.line_ids[1].credit
                            ) * (-1 if time_credit.original_value < 0 else 1))

                account = time_credit.account_depreciation_expense_id
                time_credit_depreciation = sum(
                    move.line_ids.filtered(lambda l: l.account_id == account).mapped('balance'))
                if any((line.account_id, -line.balance) ==
                       (time_credit.account_time_credit_id, time_credit.original_value) for line in move.line_ids):
                    account = time_credit.account_depreciation_id
                    time_credit_depreciation = (time_credit.original_value - time_credit.salvage_value - sum(
                        move.line_ids.filtered(lambda l: l.account_id == account).mapped(
                            'debit' if time_credit.original_value > 0 else 'credit')) *
                                                (-1 if time_credit.original_value < 0 else 1))
            move.depreciation_value_time_credit = time_credit_depreciation

    def _inverse_depreciation_value_time_credit(self):
        ''' Inverse method to update the depreciation lines amounts based on the depreciation value field.'''
        for move in self:
            time_credit = move.time_credit_id
            if time_credit:
                amount = abs(move.depreciation_value_time_credit)
                account = time_credit.account_depreciation_id
                move.write({'line_ids': [
                    Command.update(line.id, {
                        'balance': amount if line.account_id == account else -amount,
                    })
                    for line in move.line_ids
                ]})
                if time_credit.is_automatic_deferred_earnings_account:
                    account = time_credit.account_depreciation_expense_id
                    move.write({'line_ids': [
                        Command.update(line.id, {
                            'balance': amount if line.account_id == account else -amount,
                        })
                        for line in move.line_ids
                    ]})

    @api.depends('payment_state')
    def _compute_last_payment_date(self):
        ''' Compute the Last Payment Date from the invoice payments widget.'''
        for move in self:
            if move.move_type in ('in_invoice', 'out_invoice', 'out_refund', 'in_refund'):
                payments_widget_vals = move.invoice_payments_widget
                if payments_widget_vals:
                    for payment in payments_widget_vals.get('content'):
                        move.last_payment_date = payment.get('date')

    @api.depends('time_credit_id', 'depreciation_value_time_credit', 'time_credit_id.total_depreciable_value',
                     'time_credit_id.already_depreciated_amount_import')
    def _compute_depreciation_cumulative_value_time_credit(self):
        ''' Calculate the Cumulative Depreciation and Depreciable Value for related Journal Entry.'''
        self.time_credit_depreciated_value = 0
        self.time_credit_remaining_value = 0
        # make sure to protect all the records being assigned, because the
        # assignments invoke method write() on non-protected records, which may
        # cause an infinite recursion in case method write() needs to read one
        # of these fields (like in case of a base automation)
        fields = [self._fields['time_credit_remaining_value'], self._fields['time_credit_depreciated_value']]
        with self.env.protecting(fields, self.time_credit_id.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry')):
            for time_credit in self.time_credit_id:
                depreciated = 0
                remaining = time_credit.total_depreciable_value - time_credit.already_depreciated_amount_import
                filtered_depreciation_ids = time_credit.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry')
                sorted_depreciation_ids = filtered_depreciation_ids.sorted(lambda mv: (mv.date,mv._origin.id))
                for move in sorted_depreciation_ids:
                    remaining -= move.depreciation_value_time_credit
                    depreciated += move.depreciation_value_time_credit
                    move.time_credit_remaining_value = remaining
                    move.time_credit_depreciated_value = depreciated
        for time_credit in self.time_credit_id:
            remaining = 0
            filtered_depreciation_ids = time_credit.depreciation_move_ids.filtered(
                lambda move: move.move_type == 'entry')
            sorted_depreciation_ids = filtered_depreciation_ids.sorted(lambda mv: (mv.date, mv._origin.id))
            for move in sorted_depreciation_ids:
                move.sudo().time_credit_remaining_value = remaining

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def refund_moves(self):
        ''' In case of refunding an entry, Update the Credit Time Synchronization for related partners.'''
        res = super().refund_moves()
        for rec in self:
            moves = rec.move_ids
            for move in moves:
                lines = move.line_ids
                related_partners = []
                for line in lines:
                    if line.partner_id  and line.partner_id not in related_partners:
                        related_partners.append(line.partner_id)
                if len(related_partners)>0:
                    for partner in related_partners:
                        partner.update_time_credit_synchronization_for_partner(partner)
        return res

