# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_internal_invoice = fields.Boolean(compute="_compute_is_internal_invoice", default=False, store=True, copy=False)
    inter_comp_journal_entry_id = fields.Many2one('account.move', string="Related Journal Entry", copy=False,
                                                  store=True, tracking=True)
    inverse_move_type = fields.Selection([('in_invoice', 'in_invoice'), ('in_refund', 'in_refund')],
                                         compute="_compute_is_internal_invoice", store=True, copy=False)
    timesheet_for_subsidiary_ids = fields.One2many('account.analytic.line', 'subsidiary_invoice_id',
                                                   string='Subsidiary Timesheet')

    # --- Helper: ensure due dates on payable/receivable lines ---
    def _ensure_due_dates_on_moves(self):
        """Ensure every payable/receivable move line has a date_maturity.
        Use invoice_date_due -> invoice_date -> today as fallback.
        After attempting to fill, if any line still lacks date_maturity, raise a helpful ValidationError."""
        moves_checked = self
        for move in moves_checked:
            # Determine a default due date for this move
            default_due = move.invoice_date_due or move.invoice_date or fields.Date.context_today(self)
            # Fill missing date_maturity for payable/receivable lines
            for line in move.line_ids:
                acct_type = line.account_id.account_type if line.account_id else False
                if acct_type in ('liability_payable', 'asset_receivable') and not line.date_maturity:
                    try:
                        # assign fallback (try line.value_date if exists, else move due)
                        line.date_maturity = line.date_maturity or default_due
                    except Exception:
                        # in case write is forbidden due to constraints, ignore and validate afterwards
                        pass

            # Validate none remain missing
            missing = move.line_ids.filtered(
                lambda l: (l.account_id.account_type in ('liability_payable', 'asset_receivable')) and (
                    not l.date_maturity)
            )
            if missing:
                # Build a readable message
                details = []
                for l in missing:
                    details.append("line id %s (account: %s, move: %s)" % (l.id or 'new',
                                                                           l.account_id and l.account_id.code + ' ' + l.account_id.name or 'unknown',
                                                                           move.name or move.id))
                raise ValidationError(_("Missing due date for payable/receivable lines: %s") % (', '.join(details)))

    @api.depends('partner_id')
    def _compute_is_internal_invoice(self):
        """
            Determines whether an invoice is inter-company based on its partner.
            Also sets the corresponding inverse move type
            (customer invoice → vendor bill, refund → vendor refund).
        """
        for invoice in self.filtered(lambda move: move.move_type in ['out_invoice', 'out_refund','in_invoice', 'in_refund']):
            company = self.env['res.company']._find_company_from_partner(invoice.partner_id.id)
            invoice.is_internal_invoice = True if company else False
            if invoice.is_internal_invoice and invoice.move_type == 'out_invoice':
                invoice.inverse_move_type = 'in_invoice'
            elif invoice.is_internal_invoice and invoice.move_type == 'out_refund':
                invoice.inverse_move_type = 'in_refund'
            else:
                invoice.inverse_move_type = False

    def generate_related_journal_entry(self):
        """
            Creates or updates the corresponding inter-company journal entry
            for outgoing invoices or refunds linked to internal partners.
            Ensures due dates are set before posting the related entry.
        """
        for rec in self.filtered(
                lambda move: move.move_type in ('out_invoice', 'out_refund') and move.is_internal_invoice):
            invoices_map = {}
            company = self.env['res.company']._find_company_from_partner(rec.partner_id.id)
            if company:
                invoices_map.setdefault(company, self.env['account.move'])
                invoices_map[company] += rec
            for company, invoices in invoices_map.items():
                context = dict(self.env.context, default_company_id=company.id)
                context.pop('default_journal_id', None)
                move_id = invoices.with_user(SUPERUSER_ID).with_context(context).with_company(
                    company)._inter_company_create_invoices_data()
                rec.write({'inter_comp_journal_entry_id': move_id.id})
                if rec.state == 'posted':
                    move_id._ensure_due_dates_on_moves()
                    move_id.action_post()
        return True

    @api.model_create_multi
    def create(self, vals):
        """
           Generate the related inter-company journal entry when creating a new invoice or refund.
        """
        res = super(AccountMove, self.with_context(from_inter_company_transaction=True)).create(vals)
        if not res.inter_comp_journal_entry_id:
            res.generate_related_journal_entry()
        return res

    def write(self, vals):
        """
            To sync inter-company journal entries.
            Updates linked entries when invoice fields or lines are modified.
            Ensures related move lines and totals remain consistent.
        """
        old_inter_comp_journal_entry_id = self.inter_comp_journal_entry_id
        if vals.get('inter_comp_journal_entry_id', False):
            related_entry_id = self.env['account.move'].browse([vals.get('inter_comp_journal_entry_id')])
            company = self.env['res.company']._find_company_from_partner(related_entry_id.partner_id.id)
            if not company:
                raise ValidationError('Invalid partner for related entry!')
        res = super(AccountMove, self).write(vals)
        can_update_fields = ['ref', 'currency_id', 'invoice_date', 'invoice_date_due', 'payment_reference']
        for rec in self.filtered(
                lambda move: move.move_type in ['out_invoice', 'out_refund'] and move.inter_comp_journal_entry_id):
            if vals.get('inter_comp_journal_entry_id', False):
                rec.inter_comp_journal_entry_id.inter_comp_journal_entry_id = rec.id
            if vals.get('invoice_line_ids', False) or vals.get('line_ids', False):
                line_vals_list = []
                for move_line_id in rec.invoice_line_ids:
                    move_vals = move_line_id._inter_company_prepare_invoice_data_line()
                    move_vals.update({'move_id': rec.inter_comp_journal_entry_id.id})
                    line_vals_list.append(move_vals)
                rec.inter_comp_journal_entry_id.invoice_line_ids.with_context(force_delete=True).unlink()
                rec.env['account.move.line'].create(line_vals_list)
            update_related_je_vals = {}
            for key, value in vals.items():
                if key in can_update_fields:
                    update_related_je_vals.update({key: value})
            if update_related_je_vals:
                rec.inter_comp_journal_entry_id.write(update_related_je_vals)
            for line in rec.inter_comp_journal_entry_id.line_ids:
                line._compute_totals()
            for line in rec.line_ids:
                line._compute_totals()
        if not self.inter_comp_journal_entry_id and old_inter_comp_journal_entry_id:
            old_inter_comp_journal_entry_id.inter_comp_journal_entry_id = False
        return res

    def action_switch_invoice_into_refund_credit_note(self):
        """
            When an invoice is converted into a refund or credit note,
            remove the old inter-company journal entry and generate a new one
            to maintain proper synchronization.
        """
        res = super(AccountMove, self).action_switch_invoice_into_refund_credit_note()
        for rec in self:
            if rec.inter_comp_journal_entry_id:
                rec.inter_comp_journal_entry_id.unlink()
                rec.generate_related_journal_entry()
        return res

    def _inter_company_prepare_invoice(self, invoice_type):
        """
        Prepare clean and validated invoice data for inter-company creation
        with guaranteed invoice_date_due and safe fallback.
        """
        self.ensure_one()

        invoice_date = self.invoice_date or fields.Date.context_today(self)
        due_date = self.invoice_date_due

        if not due_date:
            payment_term = (self.company_id.partner_id.property_supplier_payment_term_id
                            or self.company_id.partner_id.property_payment_term_id)
            if payment_term:
                try:
                    due_date = payment_term._compute_payment_term_date(invoice_date)
                except Exception:
                    due_date = invoice_date + relativedelta(days=30)
            else:
                due_date = invoice_date + relativedelta(days=30)

        delivery_partner_id = self.company_id.partner_id.address_get(['delivery'])['delivery']
        delivery_partner = self.env['res.partner'].browse(delivery_partner_id)
        fiscal_position_id = self.env['account.fiscal.position']._get_fiscal_position(
            self.company_id.partner_id, delivery=delivery_partner
        )

        return {
            'move_type': invoice_type,
            'ref': self.ref,
            'partner_id': self.company_id.partner_id.id,
            'currency_id': self.currency_id.id,
            'inter_comp_journal_entry_id': self.id,
            'invoice_date': invoice_date,
            'invoice_date_due': due_date,
            'payment_reference': self.payment_reference,
            'invoice_origin': _('%s Invoice: %s') % (self.company_id.name, self.name),
            'fiscal_position_id': fiscal_position_id,
            # ✅ always pick a correct-type journal
            'journal_id': self.env['account.journal'].search([
                ('type', '=', 'purchase' if invoice_type == 'in_invoice' else 'sale'),
                ('company_id', '=', self.env.company.id)
            ], limit=1).id,
        }

    def _inter_company_create_invoices_data(self):
        """
        Create inter-company invoice/bill and ensure every payable/receivable line
        has a due date before write() validation.
        """
        invoices_vals_per_type = {}
        inverse_types = {
            'out_invoice': 'in_invoice',
            'out_refund': 'in_refund',
        }

        for inv in self.filtered(lambda m: m.move_type in ['out_invoice', 'out_refund']):
            invoice_vals = inv._inter_company_prepare_invoice(inverse_types[inv.move_type])
            invoice_vals['invoice_line_ids'] = []

            for line in inv.invoice_line_ids:
                vals_line = line._inter_company_prepare_invoice_data_line()
                vals_line['date_maturity'] = invoice_vals.get('invoice_date_due') or fields.Date.context_today(self)
                invoice_vals['invoice_line_ids'].append((0, 0, vals_line))

            # Convert & create invoice in target company
            inv_new = inv.with_context(default_move_type=invoice_vals['move_type']).new(invoice_vals)
            for line in inv_new.invoice_line_ids.filtered(lambda l: l.display_type not in ('line_note', 'line_section')):
                price_unit = line.price_unit
                line.tax_ids = line._get_computed_taxes()
                line.price_unit = price_unit

            invoice_vals = inv_new._convert_to_write(inv_new._cache)
            invoice_vals.pop('line_ids', None)
            invoice_vals['origin_invoice'] = inv
            invoices_vals_per_type.setdefault(invoice_vals['move_type'], [])
            invoices_vals_per_type[invoice_vals['move_type']].append(invoice_vals)

        moves = self.env['account.move']
        for invoice_type, invoices_vals in invoices_vals_per_type.items():
            for invoice in invoices_vals:
                origin_invoice = invoice.pop('origin_invoice')
                msg = _("Automatically generated from %(origin)s of company %(company)s.",
                        origin=origin_invoice.name, company=origin_invoice.company_id.name)

                am = self.with_context(default_type=invoice_type).create(invoice)


                for line in am.line_ids:
                    acct_type = line.account_id.account_type
                    if acct_type in ['liability_payable', 'asset_receivable'] and not line.date_maturity:
                        line.date_maturity = am.invoice_date_due or am.invoice_date or fields.Date.context_today(self)

                am.message_post(body=msg)
                moves += am
        return moves



    def _post(self, soft=True):
        """
            Post the current invoice and its related inter-company journal entry .
        """
        posting = super(AccountMove, self)._post(soft)
        # When posting original invoice, ensure related intercompany is posted only after safety
        for invoice in posting.filtered(
                lambda move: move.inter_comp_journal_entry_id and move.move_type in ['out_invoice', 'out_refund']):
            if invoice.inter_comp_journal_entry_id.state != 'posted':
                invoice.inter_comp_journal_entry_id._ensure_due_dates_on_moves()
                invoice.inter_comp_journal_entry_id.action_post()
        return posting

    def button_draft(self):
        """
           Resets the current invoice and its related inter-company journal entry
           to draft state.
        """
        res = super(AccountMove, self).button_draft()
        for move in self:
            if move.inter_comp_journal_entry_id and move.move_type in ['out_invoice', 'out_refund']:
                move.inter_comp_journal_entry_id.button_draft()
        return res

    def button_cancel(self):
        """
           Cancels the current invoice and its related inter-company journal entry.
        """
        res = super(AccountMove, self).button_cancel()
        if self.inter_comp_journal_entry_id and self.move_type in ['out_invoice', 'out_refund']:
            self.inter_comp_journal_entry_id.button_cancel()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _inter_company_prepare_invoice_data_line(self):
        """
        Prepares account move line values for inter-company invoices.

        Ensures:
        - Correct account mapping (income↔expense) based on move type.
        - Company consistency for target inter-company transactions.
        - Safe fallback to default income/expense accounts.
        - Due dates are set for receivable/payable lines.
        """
        self.ensure_one()
        vals = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.quantity,
            'discount': self.discount,
            'price_unit': self.price_unit,
        }

        target_company = self.env['res.company']._find_company_from_partner(self.move_id.partner_id.id)
        acct_type = self.account_id.account_type if self.account_id else None
        new_account_id = self.account_id.id if self.account_id else False

        if target_company:
            product_target = self.product_id.with_company(target_company)
            categ_target = self.product_id.categ_id.with_company(target_company)

            Account = self.env['account.account']
            domain_exp = [('account_type', '=', 'expense')]
            domain_inc = [('account_type', '=', 'income')]

            if 'company_id' in Account._fields:
                domain_exp.append(('company_id', '=', target_company.id))
                domain_inc.append(('company_id', '=', target_company.id))

            default_exp_account = Account.search(domain_exp, limit=1)
            default_inc_account = Account.search(domain_inc, limit=1)

            if self.move_id.move_type in ['in_invoice', 'in_refund'] and acct_type == 'income':
                expense_account = (
                        product_target.property_account_expense_id
                        or categ_target.property_account_expense_categ_id
                        or default_exp_account
                )
                if not expense_account:
                    raise ValidationError(
                        _(f"No valid expense account found for {product_target.display_name} "
                          f"in {target_company.name}. Please configure one.")
                    )
                new_account_id = expense_account.id

            elif self.move_id.move_type in ['out_invoice', 'out_refund'] and acct_type == 'expense':
                income_account = (
                        product_target.property_account_income_id
                        or categ_target.property_account_income_categ_id
                        or default_inc_account
                )
                if not income_account:
                    raise ValidationError(
                        _(f"No valid income account found for {product_target.display_name} "
                          f"in {target_company.name}. Please configure one.")
                    )
                new_account_id = income_account.id

            vals['company_id'] = target_company.id

        if new_account_id:
            vals['account_id'] = new_account_id

        if acct_type in ['liability_payable', 'asset_receivable']:
            vals['date_maturity'] = (
                    self.date_maturity
                    or self.move_id.invoice_date_due
                    or fields.Date.context_today(self)
            )

        return vals




