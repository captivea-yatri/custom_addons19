# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import xlsxwriter
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlwt
import io
import re


from odoo.tools.safe_eval import safe_eval


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_validate(self):
        """
        comput sheet of payslip
        """
        self.slip_ids.compute_sheet()
        return super(HrPayslipRun,  self.with_context(key='batch_payslip')).action_validate()

    def action_confirm(self):
        """
        batch should be confirm state
        """
        for record in self:
            record.write({'state': 'verify'})
            record.slip_ids.write({'state': 'verify'})

    def action_draft(self):
        """
        payslip in running state
        """
        if self.slip_ids.filtered(lambda s: s.state == 'paid'):
            raise ValidationError(
                _('You cannot reset a batch to draft if some of the payslips have already been paid.'))
        self.write({'state': 'draft'})
        self.slip_ids.write({'state': 'draft',
                             'move_id': False})

    def open_journal_entry(self):
        """
        show journal entry items in smart button
        """
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_journal_line')
        payment = self.env['account.payment'].search([('payslip_id', 'in', self.slip_ids.ids)])
        action['domain'] = [('id', 'in', self.slip_ids.move_id.ids + payment.move_id.ids)]
        action['context'] = []
        return action

    def open_journal_items(self):
        """
        show journal items in smart button
        """
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_moves_all')
        payment = self.env['account.payment'].search([('payslip_id', 'in', self.slip_ids.ids)])
        action['domain'] = [('id', 'in', self.slip_ids.move_id.line_ids.ids + payment.move_id.line_ids.ids)]
        action['context'] = []
        return action

    def register_payment(self):
        """
        register payment
        """
        for rec in self:
            return {
                'name': _('Batch Payslip Payment'),
                'res_model': 'account.payment.register',
                'view_mode': 'form',
                'context': {
                    'active_model': 'account.move',
                    'active_ids': self.slip_ids.move_id.ids,
                    'post_id': rec.id,
                    'post_model': 'hr.payslip.run',
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
            }

    def export_batches_payslip(self):
        """"
        export batch pay slip
        """
        row = 0
        col = 0
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        format2 = workbook.add_format({"font_size": 10, "align": "left", "bold": 1, "border": 1, 'bg_color': '#BFBFBF'})
        format3 = workbook.add_format({"border": 1, "align": "center", 'bg_color': '#BFBFBF', "bold": 1, })
        format1 = workbook.add_format({"font_size": 10, "align": "left", "num_format": "mm/dd/yyyy"})
        format4 = workbook.add_format({"border": 1, 'bg_color': '#BFBFBF'})
        format5 = workbook.add_format({"border": 0, 'bg_color': '#FF6600'})
        worksheet = workbook.add_worksheet("PaySlip Details")
        merge = workbook.add_format({"border": 1, "align": "center", 'bg_color': '#FF6600', "font_size": 20})
        merge.set_align('vcenter')
        merge.set_align('center')
        format2.set_align('vcenter')
        worksheet.set_tab_color('#0d0d0d')
        worksheet.merge_range("AC1:AC3", "From", merge)
        worksheet.set_column(28, 28, 120)
        worksheet.write(row, col, 'Transaction Type', format2)
        worksheet.write(row, col + 1, 'Beneficiary Code', format2)
        worksheet.write(row, col + 2, 'Beneficiary Account Number', format2)
        worksheet.write(row, col + 3, 'Transaction Amount', format2)
        worksheet.write(row, col + 4, 'Beneficiary Name', format2)
        worksheet.write(row, col + 13, 'Customer Reference Number', format2)
        worksheet.write(row, col + 22, 'VALUE DATE', format2)
        worksheet.write(row, col + 24, 'IFSC Code', format2)
        worksheet.write(row, col + 27, 'Beneficiary email id', format2)
        worksheet.set_column(13,13, 23)
        worksheet.set_column(0, 4, 25)
        worksheet.set_column(22, 22, 20)
        worksheet.set_column(24, 24, 20)
        worksheet.set_column(27, 27, 40)
        worksheet.set_row(0, 20)
        row+1
        worksheet.write(row + 1, col, '1', format3)
        worksheet.write(row + 1, col + 1, '13', format3)
        worksheet.write(row + 1, col + 2, '25', format3)
        worksheet.write(row + 1, col + 3, '20(17.2)', format3)
        worksheet.write(row + 1, col + 4, '40', format3)
        worksheet.write(row + 1, col + 13, '20', format3)
        worksheet.write(row + 1, col + 22, '10', format3)
        worksheet.write(row + 1, col + 24, '15', format3)
        worksheet.write(row + 1, col + 27, '100', format3)

        # row+1
        format2.set_text_wrap()
        worksheet.write(row + 2, col, 'R - RTGS\nN - NEFT\nI - Funds Transfer\nD - Demand Draft', format2)
        worksheet.write(row + 2, col + 1, 'A001 (Mandatory in case  HDFC  FUND Transfer)', format2)
        worksheet.write(row + 2, col + 2, 'Beneficiary Account Number', format2)
        worksheet.write(row + 2, col + 3, 'Transaction Amount', format2)
        worksheet.write(row + 2, col + 4, 'Beneficiary Name', format2)
        worksheet.write(row + 2, col + 13, ' DEBIT   NARRATION', format2)
        worksheet.write(row + 2, col + 22, '03/11/2015 (VALUE DATE )DD/MM/YYYY', format2)
        worksheet.write(row + 2, col + 24, 'IFSE CODE ', format2)
        worksheet.write(row + 2, col + 27, 'EMAIL ID OF BENIFICIARY', format2)
        worksheet.set_row(2, 50)
        worksheet.set_column('F:M', None, None, {'hidden': 1})
        worksheet.set_column('O:V', None, None, {'hidden': 1})
        worksheet.set_column('X:X', None, None, {'hidden': 1})
        worksheet.set_column('Z:AA', None, None, {'hidden': 1})

        for line in self.slip_ids:
            email = line.employee_id.work_email
            current_month = line.date_from.strftime('%B')
            current_year = line.date_from.year
            combine_month_year = f"{current_month} Salary {current_year}"

            bic = line.employee_id.bank_account_id.bank_id.bic
            if bic:
                if str(bic[:4]) == 'HDFC':
                    hdfc = 'I'
                else:
                    hdfc = 'N'
            else:
                hdfc = 'N'

            acc_number = line.employee_id.bank_account_id.acc_number
            if acc_number:
                acc_account = 'A' + str(acc_number[-3:])
            else:
                acc_account = 'A'
            line_id = line.line_ids.filtered(lambda e: e.category_id.code == 'NET')

            worksheet.write(row + 3, col, hdfc, format4)
            worksheet.write(row + 3, col + 1, acc_account if acc_account else ' ', format4)
            worksheet.write(row + 3, col + 2,
                            line.employee_id.bank_account_id.acc_number if line.employee_id.bank_account_id.acc_number else ' ',
                            format4)
            worksheet.write(row + 3, col + 3, line_id.total if line_id.total else ' ', format4)
            worksheet.write(row + 3, col + 4, line.employee_id.name if line.employee_id.name else ' ', format4)
            worksheet.write(row + 3, col + 13, combine_month_year if combine_month_year else ' ', format4)
            worksheet.write(row + 3, col + 22, line.date_from.strftime("%d/%m/%y") if line.date_from else ' ', format4)
            worksheet.write(row + 3, col + 24,
                            line.employee_id.bank_account_id.bank_bic if line.employee_id.bank_account_id.bank_bic else ' ',
                            format4)
            worksheet.write(row + 3, col + 27, line.employee_id.work_email if line.employee_id.work_email else ' ',
                            format4)


            start_row = row + 3
            start_row += 1
            formula = f'=CONCATENATE(A{start_row}&","&B{start_row}&","&C{start_row}&","&D{start_row}&","&E{start_row}&","&F{start_row}&","&G{start_row}&","&H{start_row}&","&I{start_row}&","&J{start_row}&","&K{start_row}&","&L{start_row}&","&M{start_row}&","&N{start_row}&","&O{start_row}&","&P{start_row}&","&Q{start_row}&","&R{start_row}&","&S{start_row}&","&T{start_row}&","&U{start_row}&","&V{start_row}&","&W{start_row}&","&X{start_row}&","&Y{start_row}&","&Z{start_row}&","&AA{start_row}&","&AB{start_row})'
            range_string = f'AC{start_row}:AC{start_row}'  # Properly interpolate start_row into the range string
            worksheet.write_array_formula(range_string, formula, format5)

            row += 1

        workbook.close()
        output.seek(0)
        attach = self.env["ir.attachment"].create(
            {
                "name": "Batch Payslip.xlsx",
                "datas": base64.b64encode(output.read()),
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % (attach.id),
            "target": self,
            "nodestroy": False,
        }
