# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    customer_seniority_days = fields.Integer('Customer Seniority', compute='_compute_customer_seniority_days')
    customer_seniority_type = fields.Selection([('new', 'New'),
                                                ('existing', 'Existing'),
                                                ], store=True, string="Customer Seniority Type")

    @api.depends('partner_id.customer_since_date', 'invoice_date', 'partner_id')
    def _compute_customer_seniority_days(self):
        """Compute the number of days since the customer started and assign seniority type."""
        for rec in self:
            total_days = 0
            if rec.partner_id.customer_since_date and rec.invoice_date:
                total_days = (rec.invoice_date - rec.partner_id.customer_since_date).days
            elif rec.partner_id.parent_id.customer_since_date and rec.invoice_date:
                total_days = (rec.invoice_date - rec.partner_id.parent_id.customer_since_date).days
            rec.customer_seniority_days = total_days
            if rec.customer_seniority_days > 365 and rec.customer_seniority_type != 'existing':
                rec.sudo().customer_seniority_type = 'existing'
            elif rec.customer_seniority_days <= 365 and rec.customer_seniority_type != 'new':
                rec.sudo().customer_seniority_type = 'new'

    @api.depends('bank_partner_id', 'partner_id')
    def _compute_partner_bank_id(self):
        """Determine and assign the appropriate bank account based on partner or or if not partner then from bank partner id"""
        for move in self:
            if not move.partner_id or (move.partner_id and not move.partner_id.property_company_bank_account_id):
                bank_ids = move.bank_partner_id.bank_ids.filtered(
                    lambda bank: bank.company_id is False or bank.company_id == move.company_id)
                move.partner_bank_id = bank_ids and bank_ids[0]
            else:
                move.partner_bank_id = move.partner_id.property_company_bank_account_id.id

    @api.depends('invoice_date', 'company_id')
    def _compute_date(self):
        """Override to ensure vendor bills use invoice date as the accounting date."""
        for rec in self:
            if rec.move_type in ('in_invoice') and rec.invoice_date:
                rec.date = rec.invoice_date
            else:
                super(AccountMove, self)._compute_date()


    @api.depends('move_type', 'partner_id', 'company_id')
    def _compute_narration(self):
        """
        we have changes for default function to remove narration from invoice
        @return:
        """
        pass

