# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    compensate_account_payable_id = fields.Many2one('account.account')
    compensate_account_receivable_id = fields.Many2one('account.account')
    compensate_journal_id = fields.Many2one('account.journal')
