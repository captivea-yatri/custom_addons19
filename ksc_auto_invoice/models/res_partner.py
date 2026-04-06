# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    total_security_deposit = fields.Float(string='Total Security Deposit', compute='_compute_total_security')
    desactivate_security_deposit = fields.Boolean(string='Disactivate Security Deposit')

    def fetch_partner_paid_deposit(self, security_deposit_account_ids, payment_status=[]):
        """
        Calculates the total paid security deposit for the partner, including parent/child partners.
        """
        security_amount = 0
        for partner in self:
            move_line_ids = self.sudo().env['account.move.line']
            if not partner.parent_id:
                move_line_ids = partner.get_security_move_ids(security_deposit_account_ids, False, payment_status)
                move_line_ids += partner.get_security_move_ids(security_deposit_account_ids, True)
            elif partner.parent_id:
                move_line_ids = partner.parent_id.get_security_move_ids(security_deposit_account_ids, False,
                                                                        payment_status)
                move_line_ids += partner.parent_id.get_security_move_ids(security_deposit_account_ids, True)
            if move_line_ids:
                security_amount += sum(move_line_ids.mapped('credit')) - sum(move_line_ids.mapped('debit'))
        return security_amount

    def _compute_total_security(self):
        """
        Computes the total security deposit paid by the partner across allowed companies.
        """
        company_ids = self.env.context['allowed_company_ids']
        security_deposit_account_ids = self.sudo().env['res.company'].browse(company_ids).mapped(
            'security_deposit_account_id')
        for rec in self:
            rec.total_security_deposit = rec.fetch_partner_paid_deposit(security_deposit_account_ids,
                                                                        ['paid', 'reversed'])

    def get_security_move_ids(self, security_deposit_account_ids, only_entry=False, payment_status=[]):
        """
        Fetches the security deposit journal items for this partner, filtered by account, move type, and payment state.
        """
        domain = [('account_id', 'in', security_deposit_account_ids.ids), ('partner_id', '=', self.id)]
        if only_entry:
            domain += [('move_id.move_type', '=', 'entry'), ('move_id.state', '=', 'posted')]
        else:
            domain += [('move_id.payment_state', 'in', payment_status), ('move_id.move_type', '!=', 'entry')]
        return self.env['account.move.line'].sudo().search(domain)
