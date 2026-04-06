# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'general':
            return {'domain': {'default_account_id': [('account_type','in',['liability_payable'])]}}
        else:
            return {
                'domain': {'default_account_id': [('deprecated', '=', False), ('company_id', '=', self.env.company.id),
                                                  ('account_type', '=', self.default_account_type),
                                                  ('account_type', 'not in',
                                                   ('asset_receivable', 'liability_payable'))]}}


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self.sudo()).action_create_payments()
        if self.env.context.get('hr_payroll_payment_register') == True:
            self.env['hr.payslip'].browse(self._context.get('active_id')).state = 'paid'
        #batch should be paid state if payslip has paid
        elif self.env.context.get('post_model') == 'hr.payslip.run':
            self.env['hr.payslip.run'].browse(self._context.get('active_id')).state = 'paid'
        return res
