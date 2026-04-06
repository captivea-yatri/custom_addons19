# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payslip_id = fields.Many2one('hr.payslip')

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals,force_balance)
        if self.env.context.get('post_model') == 'hr.payslip':
            for rec in res:
                rec['name'] = self.env.context.get('label')
            self.write({'payslip_id': self.env.context.get('post_id')})
        return res

    @api.model
    def _get_valid_payment_account_types(self):
        account_types = super()._get_valid_payment_account_types()
        if self.env.context.get('post_model') == 'hr.payslip.run':
            account_types.append('liability_current')
        return account_types
