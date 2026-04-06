from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_round
from odoo.tools import float_compare, float_is_zero, formatLang
import logging

_logger = logging.getLogger(__name__)


class TimeCredit(models.Model):
    _name = 'time.credit'
    _description = 'Time Credit Recognition'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']

    ######################################## BASE FIELDS  ##############################################################

    account_time_credit_id = fields.Many2one('account.account', string='Fixed Credit Account',
                                             compute='_compute_account_credit_id',
                                             help="Account used to record the purchase of the asset at its original "
                                                  "price.",
                                             store=True, readonly=False, states={'close': [('readonly', True)]},
                                             domain="[('company_ids', 'in', [company_id]), ('is_off_balance', '=', False)]")
    name = fields.Char(string='Credit Name', store=True, required=True, readonly=False, tracking=True)
    active = fields.Boolean('Active', default=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('open', 'Running'), ('close', 'Closed')],
                             string='Status', copy=False, default='draft',
                             help="When an asset is created, the status is 'Draft'.\n"
                                  "If the asset is confirmed, the status goes in 'Running' and the depreciation lines "
                                  "can be posted in the accounting.\n"
                                  "The 'On Hold' status can be set manually when you want to pause the depreciation of "
                                  "an asset for some time.\n"
                                  "You can manually close an asset when the depreciation is over.\n"
                                  "By cancelling an asset, all depreciation entries will be reversed", tracking=True)
    book_value = fields.Monetary(string='Deferred Revenue Amount', readonly=True, compute='_compute_book_value',
                                 recursive=True, store=True,
                                 help="Sum of the depreciable value, the salvage value and the book value of all value "
                                      "increase items", tracking=True)
    value_residual = fields.Monetary(string='Depreciable Value', compute='_compute_value_residual')
    salvage_value = fields.Monetary(string='Not Depreciable Value', readonly=True,
                                    help="It is the amount you plan to have that you cannot depreciate.")
    total_depreciable_value = fields.Monetary(compute='_compute_total_depreciable_value')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    depreciation_move_ids = fields.One2many('account.move', 'time_credit_id', string='Depreciation Lines', readonly=True, domain="[('move_type', '=', 'entry')]")

    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
                                 compute='_compute_journal_id', store=True, readonly=True,
                                 )
    original_value = fields.Monetary(string="Original Value", store=True, currency_field='currency_id',tracking=True
                                     )

    depreciation_entries_count = fields.Integer(compute='_compute_counts', string='# Posted Depreciation Entries')

    total_depreciation_entries_count = fields.Integer(compute='_compute_counts', string='# Depreciation Entries',
                                                      help="Number of depreciation entries (posted or not)")
    already_depreciated_amount_import = fields.Monetary(
        readonly=True,
        help="In case of an import from another software, you might need to use this field to have the right "
             "depreciation table report. This is the value that was already depreciated with entries not computed "
             "from this model")

############################################ BASE FIELDS END  ##########################################################

############################################  CUSTOM FIELDS  ###########################################################

    project_id = fields.Many2one('project.project', 'Project', copy=False)
    sale_order_id = fields.Many2one('sale.order', copy=False)
    is_automatic_deferred_earnings_account = fields.Boolean("Automatic Deferred Earnings Account")
    last_day_of_previous_month = fields.Date('Last date of previous updated month')
    is_reconciled = fields.Boolean('Is Reconciled', readonly=True)

    account_depreciation_id = fields.Many2one(comodel_name='account.account',
                                              string='Depreciation Account',
                                              readonly=True,
                                              domain="[('company_ids', '=', company_id)]",
                                              help="Account used in the depreciation entries, to decrease the asset "
                                                   "value.")
    account_depreciation_expense_id = fields.Many2one(comodel_name='account.account',
                                                      string='Expense Account',
                                                      domain="[('company_ids', '=', company_id)]",
                                                      readonly=True,
                                                      help="Account used in the periodical entries, to record a part of"
                                                           " the asset as expense.")
    value_left_of_the_previous_fiscal_period = fields.Monetary(string="value left of the previous fiscal period",
                                                               readonly=True)

    sale_order_line_ids = fields.One2many('sale.order.line','time_credit_id',string='Related Sale Order Lines')

############################################  CUSTOM FIELDS END ########################################################

############################################# CUSTOM METHODS  ##########################################################
    def create(self,vals):
        ''' Set the time credit id on related invoice on creation of time credit'''
        res = super(TimeCredit, self).create(vals)
        if vals['sale_order_id']:
            so = self.env['sale.order'].search([('id','=',vals['sale_order_id'])])
            for invoice in so.invoice_ids:
                if invoice.move_type == 'out_invoice' and invoice.state == 'posted' and invoice.payment_state != 'reversed' and not invoice.reversed_entry_id:
                    invoice.time_credit_id = res.id
        return res

    def unlink(self):
        ''' Prevent Deletion of time credit if journal entries are linked and update time credit synchronization on related partner'''
        for rec in self:
            if any(rec.depreciation_move_ids.filtered(lambda move:move.move_type == "entry")):
                raise UserError('You can not delete time credit with journal entries linked')
            related_partner = rec.sale_order_id.partner_id
            res = super(TimeCredit, rec).unlink()
            if related_partner:
                self.env['res.partner'].update_time_credit_synchronization_for_partner(related_partner)
            return res

    @api.constrains('active', 'state')
    def _check_active(self):
        ''' Prevent archiving of time credit if not closed'''
        for record in self:
            if not record.active and record.state not in ('close','open'):
                raise UserError(_('You cannot archive a record that is not closed'))

    def previous_fiscal_year(self):
        ''' Calculate value left of previous fiscal period on time credit'''
        time_credits = self
        if not self:
            time_credits = self.search([], limit=None)
        for time_credit in time_credits:
            today = fields.Date.today()
            fiscal_year = today.year if today > date(today.year, int(time_credit.company_id.fiscalyear_last_month),
                                                     int(time_credit.company_id.fiscalyear_last_day)) else today.year - 1
            fiscal_date = date(year=fiscal_year, month=int(time_credit.company_id.fiscalyear_last_month),
                               day=int(time_credit.company_id.fiscalyear_last_day))
            total_depreciation_value = sum(time_credit.depreciation_move_ids.filtered(
                lambda x: x.date <= fiscal_date).mapped('depreciation_value_time_credit'))
            time_credit.value_left_of_the_previous_fiscal_period = time_credit.original_value - total_depreciation_value


    def set_to_draft(self):
        ''' Set time credit to draft state'''
        self.write({'state': 'draft'})

    def set_to_running(self):
        ''' Set time credit to running/open state''' 
        self.write({'state': 'open'})

    def auto_reconcile_deferred_revenue_expense(self):
        """
        This function reconciles the revenue lines of deferred revenue and deferred expense with related invoice and
        related bill.
        """
        move_ids = self.env['account.move'].search(
            [('line_ids.time_credit_ids', '=', self.id),('move_type', '=', 'out_invoice')])
        if move_ids:
            move_ids_with_dr_de = self.filtered(
                lambda rec: rec.account_time_credit_id.id == self.account_depreciation_id.id
                            or rec.account_time_credit_id.id == self.account_depreciation_expense_id.id)
            if move_ids_with_dr_de:
                invoice_bill_line = move_ids.line_ids.filtered(
                    lambda rec: rec.account_id.id == self.account_time_credit_id.id)
                if invoice_bill_line:
                    revenue_line_ids = self.env['account.move'].search(
                        [('time_credit_id', '=', self.id), ('move_type', '=', 'entry')])
                    move_line = revenue_line_ids.line_ids.filtered(
                        lambda record: record.account_id.id == self.account_time_credit_id.id)
                    if move_line:
                        (invoice_bill_line + move_line).filtered_domain([('reconciled', '=', False)]).reconcile()
                        self.write({'is_reconciled': True})
                    else:
                        raise ValidationError('Revenue line not found with the same type of account!')
                else:
                    raise ValidationError('Invoice not found with the same type of account!')
            else:
                raise ValidationError('Invoice Account Mismatched')
        else:
            raise ValidationError("Invoice not found!")


    def compute_revenue_line_from_timesheet(self):
        """
        Compute revenue line for previous month of particular deferred revenue.
        It will calculate line also missing month in the past.
        for company France id = 3 it will be from 1st jan 2022. will not create for missing month in the past.
        """
        first_date_of_current_month = date.today() + relativedelta(day=1)
        last_day_of_previous_month = first_date_of_current_month + relativedelta(days=-1)

        records = self
        if records and not records.filtered(lambda tc: tc.is_automatic_deferred_earnings_account and
                                                       tc.book_value > 0 and tc.state in ['open', 'close']):
            return
        if not self:
            records = self.search([('active', '=', True), ('is_automatic_deferred_earnings_account', '=', True),
                                   ('state', 'in', ["open"]), ('book_value', '>', 0.0),
                                   ('last_day_of_previous_month', '!=', last_day_of_previous_month),('sale_order_id.invoice_ids.move_type', 'not in',['out_refund'])], limit=20)

        _logger.info("Revenue line will be proceeded for : %r" % (records))

        def must_be_processed(time_credit):
            """
            Return True if given asset must be processed, False otherwise.
            Asset must be processed if and only if:
            - It is marked for automatic deferred earnings,
            - Its state is 'open' or 'in_payment',
            - It has no depreciation line for last day of previous month.
            """
            return (all(line.date != last_day_of_previous_month for line in time_credit.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry')))

        for time_credit in records.filtered(lambda record: must_be_processed(time_credit=record)):
            sale_order_line_ids = time_credit.sale_order_line_ids
            if not sale_order_line_ids:
                continue
            # sl.product_id.x_studio_product_to_receive_1 and
            timesheet_ids = self.env["account.analytic.line"].search([('so_line', 'in', sale_order_line_ids.ids),
                                                                      ('date', '<=', last_day_of_previous_month)])
            # TODO: If need for france that it should calculate things afte 2021 then uncomment this condition
            # first_timesheet_line = timesheet_ids.sorted(key=lambda t: t.date)[0]
            # if self.company_id.id == 3 and first_timesheet_line.date < datetime.datetime(2022, 1, 1).date():
            #     timesheet_ids = timesheet_ids.filtered(lambda tm: tm.date >= datetime.datetime(2022, 1, 1).date())
            total_timesheet_amount = 0
            if not time_credit.sale_order_id.invoice_ids.filtered(
                    lambda move: move.move_type == 'out_invoice' and move.state == 'posted' and move.payment_state != 'reversed' and not move.reversed_entry_id):
                if self._context.get('automatic_entry', False):
                    _logger.warning("First Create Related invoice for %s" % _(str(time_credit.sale_order_id.name)))
                    continue
                else:
                    raise ValidationError(str(time_credit.sale_order_id.name) + ' ' + 'First Create Related invoice!')
            for line in timesheet_ids:
                so_line_price_subtotal_in_company_currency = \
                    float_round(line.so_line.price_subtotal * time_credit.sale_order_id.invoice_ids.filtered(
                        lambda move: move.move_type == 'out_invoice' and move.state == 'posted'and
                                     move.payment_state != 'reversed' and
                                     not move.reversed_entry_id)[0].currency_rate_on_invoice_confirmation,
                                precision_rounding=time_credit.sale_order_id.company_id.currency_id.rounding)
                '''Jaykishan Commenting the below code: - need to check alternative of UOM category as in v19 UOM category name is removed '''
                # if line.so_line.product_uom_id.category_id.name not in ['Working Time', 'Temps de travail',
                #                                                      'Horario de trabajo']:
                #     raise ValueError('Invalid unit of measure for line of product %s' % (line.so_line.product_id.name))
                if line.so_line.x_studio_qty_in_hours > 0:
                    total_timesheet_amount += \
                        float_round(line.unit_amount, precision_rounding=line.so_line.product_uom_id.rounding) * (
                                so_line_price_subtotal_in_company_currency / line.so_line.x_studio_qty_in_hours)
                else:
                    total_timesheet_amount += \
                        float_round(line.unit_amount, precision_rounding=line.so_line.product_uom_id.rounding) * \
                        so_line_price_subtotal_in_company_currency
            total_deprecated_amount = 0
            account = time_credit.account_depreciation_id
            for depreciation_id in time_credit.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry'):
                dpmove_credit_total = sum(
                    line.credit for line in depreciation_id.line_ids if line.account_id == account)
                dpmove_debit_total = sum(line.debit for line in depreciation_id.line_ids if line.account_id == account)
                total_deprecated_amount += dpmove_credit_total
                total_deprecated_amount -= abs(dpmove_debit_total)
            if total_deprecated_amount < total_timesheet_amount:
                if total_timesheet_amount <= time_credit.original_value:
                    move_vals = time_credit._prepare_move((total_timesheet_amount - total_deprecated_amount),
                                                          last_day_of_previous_month)
                    move = self.env['account.move'].create(move_vals)
                    if move:
                        move.action_post()
                    time_credit.write({'depreciation_move_ids': [(4, move.id)],
                                       'last_day_of_previous_month': last_day_of_previous_month,
                                       'already_depreciated_amount_import': 0})
                    _logger.info("Revenue line created for %s" % (str(time_credit.name)))
                else:
                    extra_value = total_timesheet_amount - time_credit.original_value
                    total_timesheet_amount = time_credit.original_value
                    move_vals = time_credit._prepare_move((total_timesheet_amount - total_deprecated_amount),
                                                          last_day_of_previous_month)
                    move = self.env['account.move'].create(move_vals)
                    if move:
                        move.action_post()
                    time_credit.write({'depreciation_move_ids': [(4, move.id)],
                                       'last_day_of_previous_month': last_day_of_previous_month,
                                       'already_depreciated_amount_import': 0})
                    _logger.info("Revenue line created for %s" % (str(time_credit.name)))
                    body = "Excess timesheet is been logged with value {extra_value}"
                    body = body.format(extra_value=extra_value)
                    time_credit.message_post(body=body)
            elif total_deprecated_amount == total_timesheet_amount:
                time_credit.write({'already_depreciated_amount_import':0,
                                   'last_day_of_previous_month': last_day_of_previous_month})

            elif (total_timesheet_amount - total_deprecated_amount) < 0:
                name = last_day_of_previous_month.strftime("%B %Y").capitalize()
                lise = ''
                if self.company_id.revenue_enquiry_user_id and self.company_id.revenue_enquiry_user_id.partner_id:
                    lise = '<a href="/web#model=res.partner&amp;id={id}" class="o_mail_redirect" data-oe-id="{id}" data-oe-model="res.partner" target="_blank">@{name}</a>'.format(
                        id=self.company_id.revenue_enquiry_user_id.partner_id.id,
                        name=self.company_id.revenue_enquiry_user_id.name)
                body = "{lise}<br><br><p>La ligne de revenus pour {name} est à vérifier (montant négatif).</p>"
                body = body.format(lise=lise, name=name)
                time_credit.message_post(body=body)
                time_credit.write({'already_depreciated_amount_import':(total_deprecated_amount - total_timesheet_amount),
                                   'last_day_of_previous_month': last_day_of_previous_month})

            self._cr.commit()

        for time_credit in records.filtered(lambda tc: tc.sale_order_line_ids):
            time_credit.write({'last_day_of_previous_month': last_day_of_previous_month})
            self._cr.commit()

    def _prepare_move(self, line_amount, last_date_of_previous_month):
        ''' Prepare move values for revenue line creation'''
        depreciation_date = last_date_of_previous_month
        company_currency = self.company_id.currency_id
        current_currency = self.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(line_amount, company_currency, self.company_id, depreciation_date)
        credit_name = self.name + ' (%s)' % (len(self.depreciation_move_ids) + 1)
        partner = self.env['res.partner']._find_accounting_partner(self.sale_order_id.partner_id)
        analytic_distribution = self.analytic_distribution
        move_line_1 = {
            'name': credit_name,
            'partner_id': partner.id,
            'account_id': self.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_distribution': analytic_distribution,
            'currency_id': current_currency.id,
            'amount_currency': -amount,
            'tax_ids': [],
        }
        move_line_2 = {
            'name': credit_name,
            'partner_id': partner.id,
            'account_id': self.account_depreciation_expense_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_distribution': {},
            'currency_id': current_currency.id,
            'amount_currency': amount,
            'tax_ids': [],
        }
        move_vals = {
            'partner_id': partner.id,
            'date': depreciation_date,
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'time_credit_id': self.id,
            'ref': _("%s: Depreciation", credit_name),
            'name': '/',
            'move_type': 'entry',
            'currency_id': current_currency.id,
        }
        return move_vals

    def create_activity_for_expired_time_credits(self):
        ''' Create activity for expired time credits based on company configuration'''
        time_credit_ids = self.search([('state', '=', 'open'), ('active', '=', True)])
        for time_credit in time_credit_ids:
            existing_activity = self.env['mail.activity'].sudo().search_count(
                [('summary', '=', 'Time credit is expired for this sale order, check if you need to consume it'),
                 ('res_id', '=', time_credit.sale_order_id.id),('res_model','=','sale.order')])
            if time_credit.company_id.number_of_months_after_credit_time_expires > 0 and time_credit.company_id.administrative_responsible and existing_activity == 0:
                expiry_date = time_credit.create_date.date() + relativedelta(
                    months=+ time_credit.company_id.number_of_months_after_credit_time_expires)
                if datetime.today().date() >= expiry_date:
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'res_model_id': self.env['ir.model'].sudo().search(
                            [('model', '=', 'sale.order')],
                            limit=1).id,
                        'res_id': time_credit.sale_order_id.id,
                        'user_id': time_credit.company_id.administrative_responsible.id,
                        'summary': 'Time credit is expired for this sale order, check if you need to consume it',
                    })

    ############################################# CUSTOM METHODS END  ##################################################


    ############################################  BASE METHODS  ########################################################


    @api.depends('account_depreciation_id', 'account_depreciation_expense_id')
    def _compute_account_credit_id(self):
        ''' Compute account time credit id from depreciation account'''
        for record in self:
            if not record.account_time_credit_id:
                record._onchange_account_depreciation_id()

    @api.onchange('account_depreciation_id')
    def _onchange_account_depreciation_id(self):
        # Always change the account since it is not visible in the form
        self.account_time_credit_id = self.account_depreciation_id

    @api.depends(
        'original_value', 'salvage_value',
        'depreciation_move_ids.state',
        'depreciation_move_ids.depreciation_value_time_credit',
        'depreciation_move_ids.reversal_move_ids'
    )
    def _compute_value_residual(self):
        ''' Compute residual value of time credit'''
        for record in self:
            posted_depreciation_moves = record.depreciation_move_ids.filtered(lambda mv: mv.state == 'posted' and mv.move_type == "entry")
            record.value_residual = (
                    record.original_value
                    - record.salvage_value
                    # - record.already_depreciated_amount_import
                    - sum(posted_depreciation_moves.mapped('depreciation_value_time_credit')))


    @api.depends('value_residual', 'salvage_value','original_value')
    def _compute_book_value(self):
        ''' Compute book value of time credit from residual value, original value and salvage value'''
        for record in self:
            record.book_value = record.value_residual + record.salvage_value
            if record.state == 'close' and all(move.state == 'posted' for move in record.depreciation_move_ids.filtered(lambda move:move.move_type == 'entry')):
                record.book_value -= record.salvage_value

    @api.depends('salvage_value', 'original_value')
    def _compute_total_depreciable_value(self):
        ''' Compute total depreciable value of time credit from original value and salvage value'''
        for time_credit in self:
            time_credit.total_depreciable_value = time_credit.original_value - time_credit.salvage_value

    def open_credit_entries(self):
        ''' Open time credit journal entries'''
        return {
            'name': _('Time Credit Journal Entries'),
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
            'views': [(self.env.ref('account.view_move_tree').id, 'list'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.depreciation_move_ids.filtered(lambda move:move.move_type == 'entry').ids)],
            'context': dict(self._context, create=False),
        }

    @api.depends('company_id')
    def _compute_journal_id(self):
        '''Compute journal id for time credit '''
        for time_credit in self:
            if time_credit.journal_id and time_credit.journal_id.company_id == time_credit.company_id:
                time_credit.journal_id = time_credit.journal_id
            else:
                time_credit.journal_id = self.env['account.journal'].search(
                    [('type', '=', 'general'), ('company_id', '=', time_credit.company_id.id)], limit=1)

    @api.depends('depreciation_move_ids.state')
    def _compute_counts(self):
        ''' Compute depreciation entries count and total depreciation entries count'''
        depreciation_per_asset = {
            group['time_credit_id'][0]: group['move_ids']
            for group in self.env['account.move'].read_group(
                domain=[
                    ('time_credit_id', 'in', self.ids),
                    ('state', '=', 'posted'),
                    ('id', 'in', self.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry').ids)
                ],
                fields=['move_ids:count(id)'],
                groupby=['time_credit_id'],
            )
        }
        for time_credit in self:
            time_credit.depreciation_entries_count = depreciation_per_asset.get(time_credit.id, 0)
            time_credit.total_depreciation_entries_count = len(time_credit.depreciation_move_ids.filtered(lambda move: move.move_type == 'entry'))

    @api.constrains('depreciation_move_ids')
    def _check_depreciations(self):
        ''' Check that the last depreciation line has remaining value 0 when time credit is closed'''
        for time_credit in self:
            filtered_depreciation_move_ids = time_credit.depreciation_move_ids.filtered(lambda move : move.move_type == 'entry')
            if (time_credit.state == 'open' and filtered_depreciation_move_ids
                    and not time_credit.currency_id.is_zero(filtered_depreciation_move_ids.sorted(lambda x: (x.date, x.id))[-1].asset_remaining_value)):
                raise UserError(_("The remaining value on the last depreciation line must be 0"))

    def validate(self):
        ''' On time credit validate, set state to open and post all unposted depreciation lines'''
        fields = [
            'salvage_value',
        ]
        ref_tracked_fields = self.env['time.credit'].fields_get(fields)
        self.write({'state': 'open'})
        for time_credit in self:
            tracked_fields = ref_tracked_fields.copy()
            dummy, tracking_value_ids = time_credit._mail_track(tracked_fields, dict.fromkeys(fields))
            asset_name = {'sale': (_('Time Credit revenue created'),
                                   _('A deferred revenue has been created for this move:'))}['sale']
            time_credit.message_post(body=asset_name[0], tracking_value_ids=tracking_value_ids)
            time_credit._check_depreciations()
            time_credit.depreciation_move_ids.filtered(lambda move: move.state != 'posted' and move.move_type == 'entry')._post()

    ############################################  BASE METHODS END #########################################################

