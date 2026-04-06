# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
from odoo.tools import float_compare, float_is_zero, plaintext2html
from datetime import datetime


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    partner_id = fields.Many2one('res.partner')
    is_set_account = fields.Boolean('Is Account', compute='_compute_account_check')
    has_reconciled_entries = fields.Boolean(related='move_id.has_reconciled_entries')
    date = fields.Date('Date Account',
                       readonly=False if "state not in ['draft','verify']" else True, copy=False,
                       help="Keep empty to use the period of the validation(Payslip) date.")

    def _compute_account_check(self):
        if self.line_ids:
            line = self.line_ids.filtered(lambda rec: rec.salary_rule_id.account_debit)
            if line:
                    self.write({'is_set_account': True})
            else:
                self.write({'is_set_account': False})
        else:
            self.write({'is_set_account': False})

    def _prepare_adjust_line(self, line_ids, adjust_type, debit_sum, credit_sum, date):
        res = super(HrPayslip, self)._prepare_adjust_line(line_ids, adjust_type, debit_sum, credit_sum, date)
        line = list(filter(lambda x: x['account_id'] == self.journal_id.default_account_id.id, line_ids))
        line[0]['partner_id'] = self.employee_id.partner_id.id
        line[0]['name'] = 'Salary Slip of ' + self.employee_id.name + ' Month of ' + str(self.date_from.month) + '/' + \
                          str(self.date_from.year)
        return res

    def action_payslip_done(self):
        if not any([self.employee_id.address_id, self.employee_id.user_id, self.employee_id.partner_id]):
            raise ValidationError(_("You need to set or create partner for employee."))
        return super(HrPayslip, self).action_payslip_done()

    def action_payslip_paid(self):
        for rec in self:
            if rec.date:
                try:
                    date_str = str(rec.date)
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    month = date_obj.strftime("%m")
                    year = date_obj.strftime("%Y")
                except ValueError:
                    month = 'N/A'
                    year = 'N/A'
            else:
                month = 'N/A'
                year = 'N/A'
            return {
                'name': _('Payslip Payment'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'context': {
                    'active_model': 'account.move',
                    'active_ids': rec.move_id.ids,
                    'post_id': rec.id,
                    'post_model': 'hr.payslip',
                     'label': f'Salary Slip of {rec.employee_id.name} Month of {month}/{year}'
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

    def open_journal_entries(self):
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_journal_line')
        payment = self.env['account.payment'].search([('payslip_id', '=', self.id)])
        action['domain'] = [('id', 'in', self.move_id.ids + payment.move_id.ids)]
        action['context'] = []
        return action

    def open_journal_items(self):
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_moves_all')
        payment = self.env['account.payment'].search([('payslip_id', '=', self.id)])
        action['domain'] = [('id', 'in', self.move_id.line_ids.ids + payment.move_id.line_ids.ids)]
        action['context'] = []
        return action

    def _action_create_account_move(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).payslip_run_id
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        for payslips_to_post in payslips_to_post: # for loop create journal entry for bulk pay slip also from batch

            # A payslip need to have a done state and not an accounting move.
            payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)

            # Check that a journal exists on all the structures
            if any(not payslip.struct_id for payslip in payslips_to_post):
                raise ValidationError(_('One of the contract for these payslips has no structure type.'))
            if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
                raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

            # Map all payslips by structure journal and pay slips month.
            # {'journal_id': {'month': [slip_ids]}}
            slip_mapped_data = defaultdict(lambda: defaultdict(lambda: self.env['hr.payslip']))
            for slip in payslips_to_post:
                slip_mapped_data[slip.struct_id.journal_id.id][slip.date or fields.Date().end_of(slip.date_to, 'month')] |= slip
            for journal_id in slip_mapped_data: # For each journal_id.
                for slip_date in slip_mapped_data[journal_id]: # For each month.
                    line_ids = []
                    debit_sum = 0.0
                    credit_sum = 0.0
                    date = slip_date
                    move_dict = {
                        'narration': '',
                        'ref': fields.Date().end_of(slip.date_to, 'month').strftime('%B %Y'),
                        'journal_id': journal_id,
                        'date': date,
                    }

                    for slip in slip_mapped_data[journal_id][slip_date]:
                        move_dict['narration'] += plaintext2html(slip.number or '' + ' - ' + slip.employee_id.name or '')
                        move_dict['narration'] += Markup('<br/>')
                        slip_lines = slip._prepare_slip_lines(date, line_ids)
                        line_ids.extend(slip_lines)

                    for line_id in line_ids: # Get the debit and credit sum.
                        debit_sum += line_id['debit']
                        credit_sum += line_id['credit']

                    # The code below is called if there is an error in the balance between credit and debit sum.
                    if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                        slip._prepare_adjust_line(line_ids, 'credit', debit_sum, credit_sum, date)
                    elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                        slip._prepare_adjust_line(line_ids, 'debit', debit_sum, credit_sum, date)

                    # Add accounting lines in the move
                    move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                    move = self._create_account_move(move_dict)

                    for slip in slip_mapped_data[journal_id][slip_date]:
                        slip.write({'move_id': move.id, 'date': date})
                         # raise validation error if move going to posted, before it account configuration is mandatory in rule
                        if self._context.get('key'):
                            if not move.line_ids.filtered(
                                    lambda line: line.display_type not in ('line_section', 'line_note')):
                                raise UserError(_("You need to add a line before posting. Entry: {}").format(slip.name))
                            else:
                                move.action_post()
        return True
