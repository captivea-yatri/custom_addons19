# -*- coding: utf-8 -*-

from odoo import models, fields, api, _,tools
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_round
import logging
import ast

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    count_time_credit = fields.Integer('Deferred Revenue', compute='_count_time_credit')
    deferred_revenue_status_time_credit = fields.Selection([('need_to_be_created', 'Need to be created'),
                                                            ('created', 'Created'),
                                                            ('non_appropriate', 'Non appropriate')], store=True,
                                                           string='Time Credit Deferred Revenue Status',
                                                           compute='_count_time_credit')
    revenue_closed_time_credit = fields.Boolean('Is Revenue Reconciled and Closed', copy=False)

    def sale_order_close_after_manual_reconcile(self):
        ''' This method will be called from server action to set the revenue_closed_time_credit field to True'''
        records = self.search([('state','=','sale'),('deferred_revenue_status_time_credit','=','created'),('revenue_closed_time_credit','=',False)])
        for rec in records:
            if rec.deferred_revenue_status_time_credit == 'created':
                closed_and_rec_time_credit_counter = 0
                related_time_credit = self.env['time.credit'].search([('sale_order_id', '=', rec.id)])
                for time_credit in related_time_credit:
                    if time_credit.state == 'close':
                        related_depreciation_items = time_credit.depreciation_move_ids.filtered(
                            lambda mv: mv.move_type == 'entry')
                        entry_counter = 0
                        for journal_entry in related_depreciation_items:
                            if not any(journal_entry.line_ids.filtered(lambda line: line.account_id == time_credit.account_depreciation_expense_id and line.reconciled == False)):
                                entry_counter += 1
                        if entry_counter == len(related_depreciation_items):
                            closed_and_rec_time_credit_counter += 1
                if len(related_time_credit) == closed_and_rec_time_credit_counter:
                    rec.sudo().write({'revenue_closed_time_credit': True})
            self._cr.commit()

    @api.depends('invoice_ids', 'order_line.product_id')
    def _count_time_credit(self):
        """
        This Function just count the deferred revenue for sale order
        """
        for rec in self:
            project_ids = rec.project_ids and rec.project_ids.ids or []
            project_ids += rec.order_line.mapped('project_id').ids
            if not project_ids:
                rec.deferred_revenue_status_time_credit = 'non_appropriate'
                rec.count_time_credit = 0
                continue
            time_credit_ids = rec.env['time.credit'].sudo().search([('project_id', 'in', project_ids),
                                                                    ('sale_order_id', '=', rec.id)])
            rec.count_time_credit = len(time_credit_ids.ids)
            if len(time_credit_ids) > 0:
                rec.deferred_revenue_status_time_credit = 'created'
            # TODO:Manage date statically on arrival of database
            elif rec.company_id.id == 1 and rec.date_order < datetime(2022, 2, 1):
                rec.deferred_revenue_status_time_credit = 'non_appropriate'
            elif rec.order_line.filtered(
                    lambda line: line.product_id.x_studio_product_to_receive and line.x_studio_qty_in_hours > 0 and
                                 line.product_id.service_policy == 'ordered_prepaid') and \
                    rec.amount_total > 0 and project_ids and rec.state == 'sale' and rec.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id):
                rec.deferred_revenue_status_time_credit = 'need_to_be_created'
            else:
                rec.deferred_revenue_status_time_credit = 'non_appropriate'

    def action_close_deferred_revenue_time_credit(self):
        """
        call's the function when any sale order revenue need to be closed and reconciled.
        It will first create task only if the hours are left.
        Then it will create revenue line only if there is amount to be revenue.
        At the end it will reconcile the revenue line and invoice line.
        """
        for rec in self:
            if not rec.invoice_ids.filtered(
                    lambda move: move.move_type == 'out_invoice' and move.state == 'posted' and move.payment_state != 'reversed' and not move.reversed_entry_id):
                if self._context.get('automatic_close', False):
                    _logger.warning("First Create Related invoice for %s" % _(str(rec.name)))
                    continue
                else:
                    raise ValidationError(str(rec.name) + ' ' + 'First Create Related invoice!')
            else:
                rec.sudo().create_task_time_credit()
                rec.create_revenue_line_time_credit()
                rec.reconcile_revenue_line_time_credit()

    def create_revenue_line_time_credit(self):
        """
        This function is used to create revenue line only if there is Residual Amount to Recognize on revenue is > 0.
        It will take all timesheet entry into accounting that is relevant.
        """
        project_ids = self.project_ids and self.project_ids.ids or []
        project_ids += self.order_line.mapped('project_id').ids
        time_credit_ids = self.env['time.credit'].sudo().search([('project_id', 'in', project_ids),
                                                                 ('sale_order_id', '=', self.id),
                                                                 ('is_automatic_deferred_earnings_account', '=', True)])
        first_date_of_current_month = datetime.today().date() + relativedelta(day=1)
        next_month_first_date = first_date_of_current_month + relativedelta(months=+1)
        last_day_of_current_month = next_month_first_date + relativedelta(days=-1)
        def must_be_processed(time_credit):
            """
            Return True if given asset must be processed, False otherwise.
            Asset must be processed if and only if:
            - It is marked for automatic deferred earnings,
            - Its state is 'open' or 'in_payment',
            - It has no depreciation line for last day of previous month.
            """
            return (all(move.date != last_day_of_current_month for move in time_credit.depreciation_move_ids.filtered(lambda mv:mv.move_type == 'entry')))

        for time_credit in time_credit_ids.filtered(lambda record: must_be_processed(time_credit=record) and
                                                                   record.book_value > 0.0 and
                                                                   record.sale_order_line_ids):
            if not time_credit.sale_order_id.invoice_ids:
                continue
            timesheet_ids = self.env["account.analytic.line"].search([('so_line', 'in', time_credit.sale_order_line_ids.ids)])
            total_timesheet_amount = 0
            for line in timesheet_ids:
                so_line_price_subtotal_in_company_currency = float_round((line.so_line.price_subtotal) * time_credit.sale_order_id.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation, precision_rounding=time_credit.currency_id.rounding)
                '''Jaykishan Commenting the below code: - need to check alternative of UOM category as in v19 UOM category name is removed '''
                # if line.so_line.product_uom_id.category_id.name not in ['Working Time', 'Temps de travail',
                #                                                      'Horario de trabajo']:
                #     raise ValueError(
                #         'Invalid unit of measure for line of product %s' % (line.so_line.product_id.name))
                if line.so_line.x_studio_qty_in_hours > 0:
                    total_timesheet_amount += \
                        float_round(line.unit_amount, precision_rounding=line.so_line.product_uom_id.rounding) * (
                                so_line_price_subtotal_in_company_currency / line.so_line.x_studio_qty_in_hours)
                else:
                    total_timesheet_amount += \
                        float_round(line.unit_amount, precision_rounding=line.so_line.product_uom_id.rounding) * \
                        so_line_price_subtotal_in_company_currency
            total_deprecated_amount = 0
            total_dpmove_debit_total = 0
            total_dpmove_credit_total = 0
            for depreciation_id in time_credit.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry'):
                total_dpmove_credit_total += sum(
                    line.credit for line in depreciation_id.line_ids if
                    line.account_id == time_credit.account_depreciation_id)
                total_dpmove_debit_total += sum(
                    line.debit for line in depreciation_id.line_ids if
                    line.account_id == time_credit.account_depreciation_id)
            total_deprecated_amount += total_dpmove_credit_total
            total_deprecated_amount -= total_dpmove_debit_total
            if total_deprecated_amount < total_timesheet_amount:
                if total_timesheet_amount <= time_credit.original_value:
                    move_vals = time_credit._prepare_move((total_timesheet_amount - total_deprecated_amount),
                                                          last_day_of_current_month)
                    move = self.env['account.move'].create(move_vals)
                    time_credit.write({'depreciation_move_ids': [(4, move.id)],
                                       'last_day_of_previous_month': last_day_of_current_month,
                                       'already_depreciated_amount_import': -abs(total_dpmove_debit_total)})
                    move.action_post()
                else:
                    extra_value = total_timesheet_amount - time_credit.original_value
                    total_timesheet_amount = time_credit.original_value
                    move_vals = time_credit._prepare_move((total_timesheet_amount - total_deprecated_amount),
                                                          last_day_of_current_month)
                    move = self.env['account.move'].create(move_vals)
                    time_credit.write({'depreciation_move_ids': [(4, move.id)],
                                       'last_day_of_previous_month': last_day_of_current_month,
                                       'already_depreciated_amount_import': -abs(total_dpmove_debit_total)})
                    move.action_post()
                    body = "Excess timesheet is been logged with value {extra_value}"
                    body = body.format(extra_value=extra_value)
                    time_credit.message_post(body=body)

            elif (total_timesheet_amount - total_deprecated_amount) < 0:
                time_credit.write(
                    {'already_depreciated_amount_import': total_timesheet_amount - total_deprecated_amount,
                     'last_day_of_previous_month': last_day_of_current_month})
        self._cr.commit()
        return True

    def reconcile_revenue_line_time_credit(self):
        """
        This function is used to reconcile the revenue line and invoice that is related to sale order.
        It will filter all the invoice line that is to be reconciled, which is link with the sale order line.
        It will filter all the account move line from the revenue line, which is to be reconciled.
        """
        order_line_ids = self.order_line.sudo().filtered(lambda line:
                                                         line.product_id.x_studio_product_to_receive_1 and
                                                         line.product_id.service_policy == 'ordered_prepaid' and
                                                         line.price_subtotal > 0)
        unreconciled_items = self.env['account.move.line']
        for order_line_id in order_line_ids:
            # Related Invoice
            invoice_line_ids = self.env['account.move.line']
            subtotal_of_so_line = 0.0
            missing_account_order_line_ids = order_line_id.with_company(order_line_id.order_id.company_id).filtered(lambda line:
                                                                    line.invoice_lines and line.project_id and
                                                                    not (line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id))
            if missing_account_order_line_ids:
                if self._context.get('automatic_close', False):
                    _logger.warning("Missing Income account on product of order line")
                    continue
                else:
                    raise ValidationError("Missing Income account on product of order line")
            for line in order_line_id.with_company(order_line_id.order_id.company_id):
                if line.invoice_lines and (line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id):
                    for in_line in line.invoice_lines.filtered(lambda in_line: in_line.move_id.state == 'draft'):
                        if self._context.get('automatic_close', False):
                            _logger.warning(str(line.order_id.name) + 'Related invoice is not confirmed yet!')
                            continue
                        else:
                            raise ValidationError(str(line.order_id.name) + 'Related invoice is not confirmed yet!')
                    for in_line in line.invoice_lines.filtered(
                            lambda in_line: in_line.move_id.move_type == 'out_invoice'
                                            and in_line.move_id.state == 'posted'and in_line.move_id.payment_state != 'reversed'
                                                           and not in_line.move_id.reversed_entry_id):
                        if in_line.account_id and (line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id) and \
                                in_line.product_id.id == line.product_id.id and \
                                (in_line.account_id.id == (line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id) or
                                 in_line.account_id.account_type == (line.product_id.property_account_income_id.account_type or line.product_id.categ_id.property_account_income_categ_id.account_type)):
                            if not in_line in invoice_line_ids:
                                invoice_line_ids += in_line
                    # TODO : CONVERT TO COMPANY CURRENCY BELOW VAR subtotal_of_so_line FOR MULTI-CURRENCY SCENARIO
                    subtotal_of_so_line += float_round((line.price_subtotal)*(line.order_id.invoice_ids.filtered(
                        lambda move: move.move_type == 'out_invoice'
                                     and move.state == 'posted' and move.payment_state != 'reversed'
                                     and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation),precision_rounding=line.company_id.currency_id.rounding)
                else:
                    if self._context.get('automatic_close', False):
                        _logger.warning("First Create Related invoice for %s" % _(str(line.order_id.name)))
                        continue
                    else:
                        raise ValidationError(str(line.order_id.name) + 'First Create Related invoice!')
            invoice_total = sum(line.price_subtotal for line in invoice_line_ids)
            invoice_total = float_round(invoice_total * invoice_line_ids[0].move_id.currency_rate_on_invoice_confirmation,precision_rounding=order_line_id.company_id.currency_id.rounding)
            account_ids = invoice_line_ids.mapped('account_id')
            if invoice_total > subtotal_of_so_line:
                if self._context.get('automatic_close', False):
                    for time_credit in self.env['time.credit'].sudo().search([('sale_order_id', '=', self.id)]):
                        if all(m.state == 'posted' for m in time_credit.depreciation_move_ids.filtered(
                                lambda mv: mv.move_type == 'entry')) and time_credit.book_value == 0.0:
                            time_credit.sudo().write({'state': 'close'})
                    _logger.warning('Miss match invoice line total and sale order line subtotal for order ' + str(
                        self.name) + ' Please reconcile manually !')
                    continue
                else:
                    for time_credit in self.env['time.credit'].sudo().search([('sale_order_id', '=', self.id)]):
                        if all(m.state == 'posted' for m in time_credit.depreciation_move_ids.filtered(lambda mv:mv.move_type == 'entry')) and time_credit.book_value == 0.0:
                            time_credit.sudo().write({'state': 'close'})
                    self._cr.commit()
                    raise ValidationError('Miss match invoice line total and sale order line subtotal for order ' + str(self.name)+ ' Please reconcile manually !')
            # Related Asset
            fiscal_position_acc_id = order_line_id.order_id.get_account_fiscal_position_account_time_credit(
                self.company_id.res_company_time_credit_config_ids.filtered(lambda
                                                                                rec: rec.revenue_income_account == (order_line_id.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id)).revenue_income_account,
                order_line_id.order_id.fiscal_position_id)
            time_credit_id = self.env['time.credit'].sudo().search(
                [('account_depreciation_expense_id', '=', (order_line_id.with_company(order_line_id.order_id.company_id).product_id.property_account_income_id.id or order_line_id.with_company(order_line_id.order_id.company_id).product_id.categ_id.property_account_income_categ_id.id) if not fiscal_position_acc_id else order_line_id.with_company(order_line_id.order_id.company_id).time_credit_id.account_depreciation_expense_id.id),
                 ('sale_order_id', '=', self.id),
                 ('is_automatic_deferred_earnings_account', '=',
                  True)])
            move_line_ids = self.env['account.move.line']

            for asset_line in time_credit_id.depreciation_move_ids.filtered(lambda move: move.amount_total > 0 and
                                                                                         move.state == 'posted' and move.move_type == 'entry'):
                move_line_id = asset_line.line_ids.filtered(
                    lambda ml: ml.account_id in invoice_line_ids.mapped('account_id') and
                               ml.account_type not in ['asset_cash',
                                                       'liability_credit_card',
                                                       'liability_payable',
                                                       'asset_receivable'])
                if move_line_id:
                    move_line_ids += move_line_id
            (invoice_line_ids + move_line_ids).filtered_domain([('reconciled', '=', False)]).reconcile()
            self.sudo().write({'revenue_closed_time_credit': True})
            self._cr.commit()

            for id in (invoice_line_ids + move_line_ids):
                if id not in unreconciled_items:
                    unreconciled_items += id

            if self.revenue_closed_time_credit == True:
                for time_credit in self.env['time.credit'].sudo().search([('sale_order_id', '=', self.id)]):
                    if all(m.state == 'posted' for m in time_credit.depreciation_move_ids):
                        time_credit.write({'state': 'close'})
        unreconciled_items.filtered_domain([('matching_number', '=', 'P')]).remove_move_reconcile()
        unreconciled_items.filtered_domain([('reconciled', '=', False)]).reconcile()

    def create_task_time_credit(self):
        """
        This function is used to create task for the remaining time on order line. it will create individual task for
        each line which has hours left. It will also call timesheet function to add timesheet with the same remaining
        amount.
        """
        '''Jaykishan Commenting the below code: - need to check alternative of UOM category as in v19 UOM category name is removed '''
        # Todo check how to include category filter if needed in v19 in line 299 order_line filtered lambda 
        # line.product_uom_id.category_id.name in ['Working Time', 'Temps de travail', 'Horario de trabajo'] and
        for line in self.order_line.filtered(
                lambda line: float_round(line.x_studio_remaining_quantity,
                                         precision_rounding=line.product_uom_id.rounding) > 0.00 and
                             line.product_id.x_studio_product_to_receive_1):
            if not line.project_id and line.x_studio_remaining_quantity > 0 and line.price_subtotal > 0:
                raise ValidationError('There is no Project link with this sale order line %s of order %s' % (
                    line.name, line.order_id.name))
            elif not self.company_id.closing_so_user_id:
                raise ValidationError("Please configure closing sale order user on company!")
            else:
                task_vals = {'project_id': line.project_id.id,
                             'name': 'Closing of the SO',
                             'user_ids': self.company_id.closing_so_user_id.ids,
                             'sale_line_id': line.id,
                             'allocated_hours': float_round(line.x_studio_remaining_quantity,
                                                          precision_rounding=line.product_uom_id.rounding),
                             'company_id': self.company_id.id,
                             'partner_id': self.partner_id.id}
                new_task_id = self.env['project.task'].create(task_vals)
                new_task_id.active = False
                self.create_timesheet_time_credit(new_task_id)
                self._cr.commit()
        return True

    def create_timesheet_time_credit(self, new_task_id):
        """
        This Function is used to create timesheet entry for task that is passed as a parameter.
        """
        employee_id = self.env['hr.employee'].search([('company_id', '=', self.company_id.id),
                                                      ('user_id', '=', self.company_id.closing_so_user_id.id)], limit=1)
        if not employee_id:
            raise ValidationError('Please set employee for the user %s' % (self.company_id.closing_so_user_id.name))
        timesheet_vals = {'date': datetime.today().date(),
                          'employee_id': employee_id and employee_id.id or False,
                          'name': 'Closing of the SO',
                          'unit_amount': new_task_id.allocated_hours,
                          'task_id': new_task_id.id,
                          'so_line': new_task_id.sale_line_id.id,
                          'account_id': new_task_id.project_id.account_id.id,
                          'project_id': new_task_id.project_id.id}

        self.env['account.analytic.line'].with_context(timesheet_validation=True).with_company(self.company_id).create(
            timesheet_vals)
        return True

    def get_account_fiscal_position_account_time_credit(self, src_account_id, fiscal_position_id):
        ''' This function is used to get the fiscal position account for the given source account and fiscal position.'''
        account_revenue_account_id = self.env['account.fiscal.position.account'].search(
            ['&', ('account_src_id', '=', src_account_id.id),
             ('position_id', '=', fiscal_position_id.id)], order='id desc', limit=1)
        return account_revenue_account_id

    def create_time_credit(self):
        """
        This Function create deferred revenue for the sale order.
        - It search for related account's that must be configured on company if not will have warnings.
        - Sale order state must be 'sale'.
        - Will Work only if project is linked with sale order or order line.
        """
        for so in self:
            if not so.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id):
                raise ValidationError('Please Make/Confirm invoice for the sale order %s' % (so.name))
            project_ids = so.project_ids and so.project_ids.ids or []
            project_ids += so.order_line.mapped('project_id').ids
            time_credit_ids = self.env['time.credit'].sudo().search([('project_id', 'in', project_ids),
                                                                     ('sale_order_id', '=', so.id)])

            if time_credit_ids and not self._context.get('from_server_action', False):
                raise ValidationError("Time credit revenue is already been created !")

            grouped_lines = {}
            revenue_accounts_counter = []

            for so_line in so.with_company(so.company_id).order_line:
                product = so_line['product_id']
                if product['x_studio_product_to_receive_1'] and product['service_policy'] == 'ordered_prepaid':
                    if product['property_account_income_id']:
                        if product['property_account_income_id'] in revenue_accounts_counter:
                            revenue_accounts_counter = revenue_accounts_counter
                        else:
                            revenue_accounts_counter.append(product['property_account_income_id'])
                        if product[
                            'property_account_income_id'] in so.company_id.res_company_time_credit_config_ids.revenue_income_account:
                            if product['property_account_income_id'] in grouped_lines:
                                grouped_lines[product['property_account_income_id']] += float_round(so_line.price_subtotal * (so.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation), precision_rounding=so.company_id.currency_id.rounding)
                            else:
                                grouped_lines[product['property_account_income_id']] = float_round(so_line.price_subtotal * ((so.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation)), precision_rounding=so.company_id.currency_id.rounding)
                        if product[
                            'property_account_income_id'] not in so.company_id.res_company_time_credit_config_ids.revenue_income_account:
                            if not self._context.get('need_to_create_validation', False):
                                raise ValidationError("Missing Time credit config on Company %s for account %s" % _(so.company_id.name),(so_line.product_id.property_account_income_id.name or so_line.product_id.categ_id.property_account_income_categ_id.name))
                            else:
                                _logger.warning("Missing Time credit config on Company %s" % _(so.company_id.name),
                                                self)
                                break
                        else:
                            continue
                    elif product.categ_id.property_account_income_categ_id:
                        if product.categ_id.property_account_income_categ_id in revenue_accounts_counter:
                            revenue_accounts_counter = revenue_accounts_counter
                        else:
                            revenue_accounts_counter.append(product.categ_id.property_account_income_categ_id)
                        if product.categ_id.property_account_income_categ_id in so.company_id.res_company_time_credit_config_ids.revenue_income_account:
                            if product.categ_id.property_account_income_categ_id in grouped_lines:
                                grouped_lines[product.categ_id.property_account_income_categ_id] += float_round(so_line.price_subtotal * (so.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation), precision_rounding=so.company_id.currency_id.rounding)
                            else:
                                grouped_lines[product.categ_id.property_account_income_categ_id] = float_round(so_line.price_subtotal * ((so.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation)), precision_rounding=so.company_id.currency_id.rounding)
                        if product.categ_id.property_account_income_categ_id not in so.company_id.res_company_time_credit_config_ids.revenue_income_account:
                            if not self._context.get('need_to_create_validation', False):
                                raise ValidationError(f"Missing Time credit config on Company {so.company_id.name} for account {(so_line.product_id.property_account_income_id.name or so_line.product_id.categ_id.property_account_income_categ_id.name)}")
                            else:
                                _logger.warning("Missing Time credit config on Company %s" % _(so.company_id.name),
                                                self)
                                continue
                        else:
                            continue

                    else:
                        if not self._context.get('need_to_create_validation', False):
                            raise ValidationError("Missing income account for product %s" % _(so_line.product_id.name))
                        else:
                            _logger.warning("Missing income account for product %s" % _(so_line.product_id.name), self)
                            break

            if so.partner_id.company_id.id and so.partner_id.company_id.id != so.company_id.id:
                raise ValidationError("Miss match Company of customer and sale order!")
            if not so.company_id.res_company_time_credit_config_ids:
                raise ValidationError("Missing Time credit config on Company %s" % _(so.company_id.name))

            partner = so['partner_id']
            # Check SO status
            if so['state'] != 'sale':
                raise ValidationError('Le bon de commande doit être confirmé')
            project = False
            if so.project_ids:
                project = so.project_ids[0]
            if not project:
                project_ids = so.order_line.mapped('project_id')
                if project_ids:
                    project = project_ids[0]
            # Check exist one project
            if project == False:
                raise ValidationError('Le bon de commande doit avoir un projet')

            if len(grouped_lines) == len(revenue_accounts_counter):
                for income_account_id, subtotal in grouped_lines.items():
                    # Check if the income account is configured

                    revenue_income_account_id = income_account_id
                    revenue_account_id = so.company_id.res_company_time_credit_config_ids.filtered(
                        lambda r: r.revenue_income_account == income_account_id)[0].revenue_account
                    if subtotal == 0:
                        if not self._context.get('need_to_create_validation', False):
                            raise ValidationError('Pas de produit à recevoir dans cette commande')
                        else:
                            _logger.warning("Pas de produit à recevoir dans cette commande")
                            continue

                    sale_order_line_ids = self.with_company(so.company_id).order_line.filtered(lambda sl:(sl.product_id.property_account_income_id == income_account_id or sl.product_id.categ_id.property_account_income_categ_id == income_account_id) and sl.product_id.x_studio_product_to_receive_1 == True and sl.product_id.service_policy == "ordered_prepaid")

                    if so.fiscal_position_id:
                        fiscal_position_revenue_account_id = so.get_account_fiscal_position_account_time_credit(
                            revenue_account_id,
                            so.fiscal_position_id)
                        fiscal_position_revenue_income_account_id = so.get_account_fiscal_position_account_time_credit(
                            revenue_income_account_id, so.fiscal_position_id)
                        revenue_account_id = (fiscal_position_revenue_account_id and
                                              fiscal_position_revenue_account_id.account_dest_id or revenue_account_id)
                        revenue_income_account_id = (fiscal_position_revenue_income_account_id and
                                                     fiscal_position_revenue_income_account_id.account_dest_id or revenue_income_account_id)
                    new_credit_id = self.env['time.credit'].sudo().create(
                        {'name': partner['name'] + ' - ' + self['name'] + ' - ' + self.with_company(so.company_id).order_line.filtered(lambda
                                                                                                               line: (line.product_id.property_account_income_id == income_account_id or line.product_id.categ_id.property_account_income_categ_id == income_account_id)).product_id.mapped('name')[0],
                         'project_id': project and project.id or False,
                         'active': True,
                         'is_automatic_deferred_earnings_account': True,
                         'account_depreciation_id': revenue_account_id.id,
                         'account_depreciation_expense_id': revenue_income_account_id.id,
                         'journal_id': self.company_id.res_company_time_credit_config_ids.filtered(
                             lambda tcc: tcc.revenue_income_account == income_account_id).journal_id.id,
                         'original_value': subtotal,
                         'sale_order_id': self.id,
                         'company_id': self.company_id.id,
                         # 'currency_id': self.currency_id ,
                                        # and self.currency_id.id or
                                        # self.company_id.currency_id.id,
                         'sale_order_line_ids': sale_order_line_ids
                         })
                    new_credit_id.validate()
                    self.sudo()._count_time_credit()
            partner = self.env['res.partner']._find_accounting_partner(so.partner_id)
            partner.update_time_credit_synchronization_for_partner(partner)

    def action_open_deferred_revenue_time_credit(self):
        ''' This function open the deferred revenue time credit records created for the sale order.'''
        project_ids = self.project_ids and self.project_ids.ids or []
        project_ids += self.order_line.mapped('project_id').ids
        time_credit_ids = self.env['time.credit'].sudo().search([('project_id', 'in', project_ids),
                                                                 ('sale_order_id', '=', self.id)])
        if not time_credit_ids:
            raise ValidationError(_('No Deferred Revenue Found!'))
        return {'name': _('Time Credit'),
                'view_type': 'form',
                'view_mode': 'list,form',
                'res_model': 'time.credit',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', time_credit_ids.ids)],
                }

    def create_need_to_be_created_time_credit(self):
        """
        this method creates deferred revenue of sale orders which is in need to be created state.
        """
        company_ids = self.env['res.company'].search([('res_company_time_credit_config_ids', '!=', False)])
        date_after_create_revenue = datetime(2023, 1, 1)
        sale_order_ids = self.search([('company_id', 'in', company_ids.ids),
                                      ('deferred_revenue_status_time_credit', '=', 'need_to_be_created'),
                                      ('state', '=', 'sale'),
                                      ('date_order', '>=', date_after_create_revenue)])
        for sale_order_id in sale_order_ids:
            if not sale_order_id.invoice_ids or not sale_order_id.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id):
                continue

            project_ids = sale_order_id.with_company(sale_order_id.company_id).project_ids and sale_order_id.with_company(sale_order_id.company_id).project_ids.ids or []
            project_ids += sale_order_id.with_company(sale_order_id.company_id).order_line.mapped('project_id').ids
            time_credit_ids = self.env['time.credit'].sudo().search([('project_id', 'in', project_ids),
                                                                     ('sale_order_id', '=', sale_order_id.id)])

            if project_ids and not time_credit_ids:
                total_amount = 0
                sale_order_lines = sale_order_id.with_company(sale_order_id.company_id).mapped('order_line')
                for sale_order_line in sale_order_lines:
                    product = sale_order_line['product_id']
                    if product['x_studio_product_to_receive_1'] and product['service_policy'] == 'ordered_prepaid':
                        total_amount += sale_order_line['price_subtotal']
                if total_amount != 0:
                    sale_order_id.with_context(
                        need_to_create_validation=True).with_company(sale_order_id.company_id).create_time_credit()
                    deferred_revenues = self.env['time.credit'].search([('sale_order_id', '=', sale_order_id.id)])
                    deferred_revenues.validate()

    def automatically_close_time_credit(self):
        """
        This function close deferred revenue automatically which is created with sale order.
        This function close only those sale orders deferred revenue which sale orders total remaining quantity is less
        than 0.04.
        """
        not_considered_so = self.search(
            ['|',('state', 'in', ['sale']),('locked','=',True), '|',('invoice_ids.move_type','in',['out_refund']),
                 ('order_line.product_id.property_account_income_id', '=', False), ('order_line.product_id.categ_id.property_account_income_categ_id', '=', False),
             ('order_line.product_id.property_account_income_id.account_type', 'not in',
              ['asset_current', 'asset_non_current', 'liability_current', 'liability_non_current','income']),('order_line.product_id.categ_id.property_account_income_categ_id.account_type', 'not in',
              ['asset_current', 'asset_non_current', 'liability_current', 'liability_non_current','income'])])
        orders = self.search(
            [('deferred_revenue_status_time_credit', '=', 'created'), ('total_remaining_qty', '<', 0.04),
             ('revenue_closed_time_credit', '=', False), ('id', 'not in', not_considered_so.ids)], limit=20)
        for order in orders:
            if not order.invoice_ids or any(order.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and (move.payment_state == 'reversed'
                                                           or move.reversed_entry_id))):
                continue
            subtotal_of_so_line = 0.0
            project_ids = order.project_ids and order.project_ids.ids or []
            project_ids += order.order_line.mapped('project_id').ids
            if order.order_line.mapped('project_id').active == False:
                continue
            time_credit_ids = self.env['time.credit'].sudo().search([('project_id', 'in', project_ids),
                                                                     ('sale_order_id', '=', order.id)])
            if time_credit_ids:
                order_line_ids = order.order_line.sudo().filtered(
                    lambda line: line.product_id.x_studio_product_to_receive_1
                                 and line.product_id.service_policy ==
                                 'ordered_prepaid' and line.project_id)
                invoice_line_ids = self.env['account.move.line']
                for line in order_line_ids:
                    if line.invoice_lines and (line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id) and line.project_id:
                        for in_line in line.invoice_lines.filtered(
                                lambda in_line: in_line.move_id.move_type == 'out_invoice' and
                                                in_line.move_id.state == 'posted' and
                                                in_line.account_id.reconcile == True):
                            if in_line.account_id and (line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id) and \
                                    in_line.product_id.id == line.product_id.id and \
                                    (
                                            (in_line.account_id.id == line.product_id.property_account_income_id.id or in_line.account_id.id == line.product_id.categ_id.property_account_income_categ_id.id) or
                                            (in_line.account_id.account_type == line.product_id.property_account_income_id.account_type or in_line.account_id.account_type == line.product_id.categ_id.property_account_income_categ_id.account_type)):
                                if not in_line in invoice_line_ids:
                                    invoice_line_ids += in_line
                            subtotal_of_so_line += float_round(line.price_subtotal * order.invoice_ids.filtered(lambda move: move.move_type == 'out_invoice'
                                            and move.state == 'posted'and move.payment_state != 'reversed'
                                                           and not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation, precision_rounding=order.company_id.currency_id.rounding)
                            invoice_total = sum(line.credit for line in invoice_line_ids)
                            if invoice_total <= subtotal_of_so_line:
                                if order.total_remaining_qty < 0.04 and order.total_remaining_qty != 0.04:
                                    order.with_context(automatic_close = True).action_close_deferred_revenue_time_credit()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # @api.depends('order_id', 'product_id')
    # def _compute_skip_product_id_domain(self):
    #     for rec in self:
    #         product_property_ids = self.env['ir.property'].sudo().search([('name', '=', 'skip_for_sale_ok'),
    #                                                                       ('company_id', '=', self.env.company.id)])
    #         product_tmpl_ids = self.env['product.template'].sudo().search(
    #             [('id', 'in', [int(property.res_id.rsplit(',', 1)[1]) for property in product_property_ids])])
    #         rec.skip_product_id_domain = product_tmpl_ids and product_tmpl_ids.product_variant_ids.ids or False

    @api.depends('order_id', 'product_id','product_id.product_tmpl_id.skip_for_sale_ok')
    def _compute_skip_product_id_domain(self):
        ''' Compute the domain of products to skip for sale order line based on the skip_for_sale_ok field on product template.'''
        for rec in self:
            # Fetch product templates with skip_for_sale_ok=True for the current company
            product_tmpl_ids = self.env['product.template'].with_company(self.env.company).search([
                ('skip_for_sale_ok', '=', True),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', self.env.company.id)
            ])
            rec.skip_product_id_domain = product_tmpl_ids.mapped('product_variant_ids').ids if product_tmpl_ids else False

    skip_product_id_domain = fields.One2many('product.product', 'skip_for_so_line_id', 'Product Id Domain',
                                             compute="_compute_skip_product_id_domain")
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 domain="[('sale_ok', '=', True), '|', ('company_id', '=', False),('company_id', '=', company_id), ('id', 'not in', skip_product_id_domain)]",
                                 change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    emp_filter_domain = fields.Char(string='Limited To Employee', store=True, compute='compute_emp_restriction_filter')
    so_line_quota_ids = fields.One2many(comodel_name='sale.order.line.quota', inverse_name='so_line_id',
                                        string='So Quota')
    time_credit_id = fields.Many2one('time.credit', string="Related Time Credit")

    @api.depends('product_id')
    def compute_emp_restriction_filter(self):
        """
        Method compute employee filter from the product if exist on product
        """
        for rec in self:
            if rec.emp_filter_domain:
                return
            if rec.product_id and rec.product_id.emp_filter_domain:
                rec.emp_filter_domain = rec.product_id.emp_filter_domain

    def open_sale_order_line_form_view(self):
        """
        Open the custom form view that only shows the employee filter
        """
        self.ensure_one()
        return {
            'name': _('Sale order line'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sale.order.line',
            'view_id': self.env.ref('cap_automatic_deferred_earnings_account.view_order_form_line_domain_filter').id,
            'res_id': self.id,
            'target': 'new',
        }


class SaleOrderLineQuota(models.Model):
    _name = 'sale.order.line.quota'
    _description = 'Sale Order Line Quota'
    _rec_name = 'so_line_id'

    so_line_id = fields.Many2one('sale.order.line', string='So Quota')
    # TODO : As we filtered the records on this fields from below method which is not working in v18
    # After live we need to check and fix it
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    # domain = lambda self: self._domain_employee()
    hrs_qty = fields.Float(string='Hours Qty')

    # @api.onchange('employee_id')
    # def _domain_employee(self):
    #     if self.so_line_id.emp_filter_domain:
    #         domain = ast.literal_eval(self.so_line_id.emp_filter_domain)
    #         return {'domain': {'employee_id': domain}}
    #     else:
    #         return {'domain': {'employee_id': []}}

    _sql_constraints = [
        ('unique_employee_per_so_line', 'unique (so_line_id,employee_id)',
         'Only one quota per employee, per line is allowed!'),
    ]

class ResUsers(models.Model):
    _inherit = 'res.users'

    override_filter = fields.Boolean(string='Override Filter For Sale order line', help='Select if you want to override timesheet restriction functionality for employee')
