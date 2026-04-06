from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AutoCompensate(models.TransientModel):
    _name = "ksc.auto.compensate"
    _description = 'KSC Auto Compensation'

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id,
                                  required=True)
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    invoice_bill_ids = fields.One2many('auto.compensate.inv.bill', 'compensate_id', string="Invoice/Vendor Bills")

    def do_reconcile(self):
        current_inv_bill_move_line_id = self.env['account.move'].browse(
            self._context.get('active_id')).line_ids.filtered(
            lambda invl: invl.account_id.account_type == 'asset_receivable' or
                         invl.account_id.account_type == 'liability_payable')
        if current_inv_bill_move_line_id.company_id.compensate_account_payable_id and current_inv_bill_move_line_id.company_id.compensate_account_receivable_id and current_inv_bill_move_line_id.company_id.compensate_journal_id.id:
            inv_bill_ids = self.env['account.move.line']
            for rec in self.invoice_bill_ids.filtered(lambda in_bl: in_bl.is_select == True):
                inv_bill_ids |= rec.inv_bill_id.line_ids.filtered(
                    lambda invl: invl.account_id.account_type == 'asset_receivable' or
                                 invl.account_id.account_type == 'liability_payable')

            acc_payable_id = current_inv_bill_move_line_id.company_id.compensate_account_payable_id
            acc_receivable_id = current_inv_bill_move_line_id.company_id.compensate_account_receivable_id

            if inv_bill_ids and current_inv_bill_move_line_id:
                line_ids = []
                acc_pay_code_name = acc_payable_id.code + ' ' + acc_payable_id.name
                acc_rec_code_name = acc_receivable_id.code + ' ' + acc_receivable_id.name
                ref = ''
                if abs(current_inv_bill_move_line_id.amount_residual) > abs(
                        sum(inv_bill.amount_residual for inv_bill in inv_bill_ids)):
                    if current_inv_bill_move_line_id.move_id.move_type == 'in_invoice' and all(
                            inv_bill.move_id.move_type == 'out_invoice' for inv_bill in inv_bill_ids):
                        ref = 'Transfer entry to ' + acc_pay_code_name
                        line_ids.append((0, 0,
                                         {'account_id': acc_payable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer counterpart',
                                          'credit': 0.0,
                                          'debit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                       abs(sum(
                                                           inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                        line_ids.append((0, 0,
                                         {'account_id': acc_receivable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer to ' + acc_pay_code_name,
                                          'debit': 0.0,
                                          'credit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                        abs(sum(
                                                            inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                    elif current_inv_bill_move_line_id.move_id.move_type == 'out_invoice' and all(
                            inv_bill.move_id.move_type == 'in_invoice' for inv_bill in inv_bill_ids):
                        ref = 'Transfer entry to ' + acc_rec_code_name
                        line_ids.append((0, 0,
                                         {'account_id': acc_receivable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer counterpart',
                                          'debit': 0.0,
                                          'credit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                        abs(sum(
                                                            inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                        line_ids.append((0, 0,
                                         {'account_id': acc_payable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer to ' + acc_rec_code_name,
                                          'credit': 0.0,
                                          'debit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                       abs(sum(
                                                           inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                elif abs(current_inv_bill_move_line_id.amount_residual) < abs(
                        sum(inv_bill.amount_residual for inv_bill in inv_bill_ids)):
                    if current_inv_bill_move_line_id.move_id.move_type == 'in_invoice' and all(
                            inv_bill.move_id.move_type == 'out_invoice' for inv_bill in inv_bill_ids):
                        ref = 'Transfer entry to ' + acc_rec_code_name
                        line_ids.append((0, 0,
                                         {'account_id': acc_receivable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer counterpart',
                                          'debit': 0.0,
                                          'credit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                        abs(sum(
                                                            inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                        line_ids.append((0, 0,
                                         {'account_id': acc_payable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer to ' + acc_rec_code_name,
                                          'credit': 0.0,
                                          'debit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                       abs(sum(
                                                           inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                    elif current_inv_bill_move_line_id.move_id.move_type == 'out_invoice' and all(
                            inv_bill.move_id.move_type == 'in_invoice' for inv_bill in inv_bill_ids):
                        ref = 'Transfer entry to ' + acc_pay_code_name
                        line_ids.append((0, 0,
                                         {'account_id': acc_payable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer counterpart',
                                          'credit': 0.0,
                                          'debit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                       abs(sum(
                                                           inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                        line_ids.append((0, 0,
                                         {'account_id': acc_receivable_id.id,
                                          'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                          'name': 'Transfer to ' + acc_pay_code_name,
                                          'debit': 0.0,
                                          'credit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                        abs(sum(
                                                            inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                else:
                    ref = 'Transfer entry to ' + acc_pay_code_name
                    line_ids.append((0, 0, {'account_id': acc_receivable_id.id,
                                            'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                            'name': 'Transfer counterpart', 'debit': 0.0,
                                            'credit': min(abs(current_inv_bill_move_line_id.amount_residual), abs(sum(
                                                inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                    line_ids.append((0, 0, {'account_id': acc_payable_id.id,
                                            'partner_id': current_inv_bill_move_line_id.partner_id.id,
                                            'name': 'Transfer to ' + acc_pay_code_name, 'credit': 0.0,
                                            'debit': min(abs(current_inv_bill_move_line_id.amount_residual),
                                                         abs(sum(
                                                             inv_bill.amount_residual for inv_bill in inv_bill_ids)))}))
                counterpart_je_vals = {'ref': ref,
                                       'date': fields.Datetime.now(),
                                       'journal_id': current_inv_bill_move_line_id.company_id.compensate_journal_id.id,
                                       'line_ids': line_ids,
                                       'company_id': current_inv_bill_move_line_id.company_id.id,
                                       }
                counterpart_journal_entry_id = self.env['account.move'].create(counterpart_je_vals)
                counterpart_journal_entry_id.action_post()
                if current_inv_bill_move_line_id.move_id.move_type == 'in_invoice':
                    payable_cibmvl_id = current_inv_bill_move_line_id.filtered(
                        lambda invl: invl.account_id.account_type == 'liability_payable')
                    payable_cp_jl_id = counterpart_journal_entry_id.line_ids.filtered(
                        lambda invl: invl.account_id.account_type == 'liability_payable')
                    payable_reconcile = (payable_cibmvl_id + payable_cp_jl_id).filtered_domain(
                        [('reconciled', '=', False)]).reconcile()

                    receivable_inv_bill_id = inv_bill_ids.filtered(
                        lambda invl: invl.account_id.account_type == 'asset_receivable')
                    receivable_cp_jl_id = counterpart_journal_entry_id.line_ids.filtered(
                        lambda invl: invl.account_id.account_type == 'asset_receivable')
                    receivable_reconcile = (receivable_inv_bill_id + receivable_cp_jl_id).filtered_domain(
                        [('reconciled', '=', False)]).reconcile()

                elif current_inv_bill_move_line_id.move_id.move_type == 'out_invoice':
                    payable_inv_bill_id = inv_bill_ids.filtered(
                        lambda invl: invl.account_id.account_type == 'liability_payable')
                    payable_cp_jl_id = counterpart_journal_entry_id.line_ids.filtered(
                        lambda invl: invl.account_id.account_type == 'liability_payable')
                    payable_reconcile = (payable_inv_bill_id + payable_cp_jl_id).filtered_domain(
                        [('reconciled', '=', False)]).reconcile()

                    receivable_cibmvl_id = current_inv_bill_move_line_id.filtered(
                        lambda invl: invl.account_id.account_type == 'asset_receivable')
                    receivable_cp_jl_id = counterpart_journal_entry_id.line_ids.filtered(
                        lambda invl: invl.account_id.account_type == 'asset_receivable')
                    receivable_reconcile = (receivable_cibmvl_id + receivable_cp_jl_id).filtered_domain(
                        [('reconciled', '=', False)]).reconcile()
            else:
                raise ValidationError(_("Please select Customer Invoice/Vendor Bill for further processing!"))
        else:
            raise ValidationError(_("Please configure compensation journal & compensation accounts in settings!"))


class AutoCompensateInvBill(models.TransientModel):
    _name = "auto.compensate.inv.bill"
    _description = 'KSC Auto Compensate Invoice Bill'

    is_select = fields.Boolean(string="Select")
    currency_id = fields.Many2one("res.currency", string="Currency",
                                  required=True)
    inv_bill_number = fields.Char(string="Invoice/Bill Number")
    inv_bill_id = fields.Many2one('account.move', string="Invoices/Bills")
    inv_bill_amount = fields.Monetary(string="Invoice/Bill Amount", currency_field="currency_id")
    is_partial_paid = fields.Boolean("Is Partially Paid?", readonly=True)
    compensate_id = fields.Many2one("ksc.auto.compensate", string="Compensate")
