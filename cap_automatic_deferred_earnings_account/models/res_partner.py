# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_time_balance = fields.Float(compute='_compute_credit_time_balance', string='Credit Time Balance',store=True)
    deferred_revenue_balance = fields.Float(compute='_compute_deferred_revenue_balance', string='Deferred Revenue Balance',store=True)
    credit_time_synchronized = fields.Boolean(compute='_compute_credit_time_synchronized',string="Synchronization Status",store=True)

    @api.depends('credit_time_balance', 'deferred_revenue_balance', 'sale_order_ids', 'invoice_ids',
                 'invoice_ids.state')
    def _compute_credit_time_synchronized(self):
        ''' Calculate the Credit Time Synchronized for related partners.'''
        for rec in self:
            if rec.is_company or not rec.parent_id:
                if float_round(rec.credit_time_balance, precision_rounding=0.01) == float_round(
                        rec.deferred_revenue_balance, precision_rounding=0.01):
                    rec.sudo().credit_time_synchronized = True
                else:
                    rec.sudo().credit_time_synchronized = False
            else:
                rec.sudo().credit_time_synchronized = rec.parent_id.credit_time_synchronized

    def _get_all_parent_id(self):
        """Recursively fetch all parent partners."""
        self.ensure_one()
        all_parent_id = []
        current_partner = self
        while current_partner.parent_id:
            all_parent_id.append(current_partner.parent_id)
            current_partner = current_partner.parent_id
        return all_parent_id

    def get_all_child_partners(self):
        """Recursively fetch all child partners."""
        self.ensure_one()
        all_partners = self.child_ids
        for child in self.child_ids:
            all_partners |= child.sudo().get_all_child_partners()
        return all_partners

    @api.depends('child_ids','sale_order_ids','sale_order_count','invoice_ids','invoice_ids.state','invoice_ids.line_ids')
    def _compute_credit_time_balance(self):
        ''' Calculate the Credit Time Balance for related partners.'''
        for rec in self:
            if rec.is_company or not rec.parent_id:
                all_partners = rec | rec.sudo().get_all_child_partners()
                sale_order_ids = self.env['sale.order'].sudo().search(
                    [('partner_id', 'in', all_partners.ids), ('state', '=', 'sale')])
                deferred_revenue_amount_for_partner = 0.0
                if sale_order_ids:
                    related_time_credits = self.env['time.credit'].sudo().search(
                        [('sale_order_id', 'in', sale_order_ids.ids)])
                    if related_time_credits:
                        for time_credit in related_time_credits:
                            deferred_revenue_amount_for_partner += time_credit.book_value
                rec.sudo().credit_time_balance = deferred_revenue_amount_for_partner
            else:
                rec.sudo().credit_time_balance = 0.0

    @api.depends('child_ids', 'sale_order_ids', 'sale_order_count','invoice_ids','invoice_ids.state','invoice_ids.line_ids')
    def _compute_deferred_revenue_balance(self):
        ''' Calculate the Deferred Revenue Balance for related partners.'''
        for rec in self:
            if rec.is_company or not rec.parent_id:
                all_partners = rec | rec.get_all_child_partners()
                sale_order_ids = self.env['sale.order'].sudo().search(
                    [('partner_id', 'in', all_partners.ids), ('state', '=', 'sale')])
                moves = self.env['account.move'].sudo().search(
                    [('partner_id', 'in', all_partners.ids), ('state', '=', 'posted'),
                     ('move_type', 'in', ['out_invoice', 'entry', 'out_refund'])])
                related_companies = []
                for so in sale_order_ids:
                    if so.company_id not in related_companies:
                        related_companies.append(so.company_id)
                for move in moves:
                    if move.company_id not in related_companies:
                        related_companies.append(move.company_id)
                credit = 0.0
                debit = 0.0
                deferred_revenue_accounts_for_partner = []
                for company in related_companies:
                    for time_credit_config in company.res_company_time_credit_config_ids:
                        for account in time_credit_config.revenue_income_account:
                            if account.id not in deferred_revenue_accounts_for_partner:
                                deferred_revenue_accounts_for_partner.append(account.id)
                            related_fiscal_position_account = self.env['account.fiscal.position.account'].sudo().search(
                                [('account_src_id', '=', account.id)])
                            for fiscal_pos_account in related_fiscal_position_account:
                                if fiscal_pos_account.account_dest_id.id not in deferred_revenue_accounts_for_partner:
                                    deferred_revenue_accounts_for_partner.append(fiscal_pos_account.account_dest_id.id)
                if len(deferred_revenue_accounts_for_partner) > 0:
                    related_journal_items = self.env['account.move.line'].sudo().search(
                        [("move_id.state", "=", "posted"), ('partner_id', 'in', all_partners.ids),
                         ('account_id', 'in', deferred_revenue_accounts_for_partner),
                         ('move_id.move_type', 'in', ['out_invoice', 'entry', 'out_refund'])])
                    for journal_item in related_journal_items:
                        credit += journal_item.credit
                        debit += journal_item.debit
                rec.sudo().deferred_revenue_balance = credit - debit
            else:
                rec.sudo().deferred_revenue_balance = 0.0

    def update_time_credit_synchronization_for_partner(self, partner_id):
        ''' This method is call multiple places to update the Deferred Revenue Balance, Credit Time Balance and Credit Time Synchronized for all partners.'''
        all_related_partners = []
        if partner_id.is_company:
            all_related_partners.append(partner_id)
            all_parents_of_partner = partner_id.sudo()._get_all_parent_id()
            for partner in all_parents_of_partner:
                if partner not in all_related_partners:
                    all_related_partners.append(partner)
        else:
            all_parents_of_partner = partner_id.sudo()._get_all_parent_id()
            if not all_parents_of_partner:
                all_related_partners.append(partner_id)
            for partner in all_parents_of_partner:
                if partner not in all_related_partners:
                    all_related_partners.append(partner)
        for partner in all_related_partners:
            partner.sudo()._compute_credit_time_balance()
            partner.sudo()._compute_deferred_revenue_balance()
            partner.sudo()._compute_credit_time_synchronized()
