# coding: utf-8
from odoo import _, api, fields, models
import calendar
import math
from dateutil.relativedelta import relativedelta
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    automatically_invoice = fields.Selection(
        [
            ('not_activate', 'Not activated'),
            ('activated_last_day_months', 'Activated last day of the month'),
            ('activated_specific_day', 'Activated at the specific day')
        ],
        string='Automatically Invoice',
        default='not_activate'
    )
    day_of_months = fields.Integer(string='Day Of Months', default=1)
    invoice_action = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('confirmed_and_send', 'Confirmed And Send')],
        default='draft'
    )
    minimum_amount_invoice = fields.Float(string='Minimum amount to invoice', default=200)
    note = fields.Html(
        string="Terms and conditions",
        compute='_compute_note',
        store=True, readonly=False, precompute=True, copy=False
    )

    # -------------------------------------------------------------
    #   Confirm order
    # -------------------------------------------------------------
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        context = dict(self._context)
        context.update({
            'active_id': self.ids[0],
            'active_ids': self.ids,
            'open_invoices': True,
            'skip_security_deposit': True
        })
        return res

    # -------------------------------------------------------------
    #   Field validations
    # -------------------------------------------------------------
    @api.constrains('day_of_months', 'minimum_amount_invoice')
    def raise_validation_day_of_months(self):
        """Validate days and minimum amount."""
        if self.automatically_invoice == 'activated_specific_day':
            if self.day_of_months > 31 or self.day_of_months <= 0:
                raise ValidationError(f"Please Add Valid Day for this Order {self.name}")
        if self.minimum_amount_invoice < 0:
            raise ValidationError(f"Negative Amount is not Allowed {self.name}")

    # -------------------------------------------------------------
    #   Create Security Deposit Invoice Line
    # -------------------------------------------------------------
    def create_deposit_invoice_line(self, invoice_id, price_unit, security_deposit_account_id):
        """Prepare deposit line values and create it."""
        related_project = self.env['project.project'].search([
            '|',
            ('sale_order_id', '=', self.id),
            ('id', 'in', self.with_context(active_test=False).project_ids.ids),
            ('active', 'in', [True, False])
        ], limit=1)

        vals = {
            'move_id': invoice_id.id,
            'product_id': False,
            'name': 'Security Deposit',
            'quantity': 1,
            'account_id': security_deposit_account_id.id,
            'price_unit': price_unit,
        }
        if related_project and related_project.account_id:
            vals['analytic_distribution'] = {related_project.account_id.id: 100}
        self.env['account.move.line'].create(vals)

    # -------------------------------------------------------------
    #   Override to insert security deposit logic
    # -------------------------------------------------------------
    def _create_invoices(self, grouped=False, final=False, date=None):
        """Extend invoice creation to automatically add security deposit line."""
        invoices = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)

        for order in self:
            for invoice in invoices.filtered(
                lambda inv: inv.move_type == 'out_invoice' and inv.partner_id == order.partner_id
            ):
                # Ensure invoice totals & lines are fully computed
                if hasattr(invoice, '_recompute_fields'):
                    try:
                        invoice._recompute_fields()
                    except Exception as e:
                        print("⚠️ _recompute_fields() raised:", e)
                elif hasattr(invoice, '_recompute_dynamic_lines'):
                    try:
                        invoice._recompute_dynamic_lines(recompute_all_taxes=True)
                    except Exception as e:
                        print("⚠️ _recompute_dynamic_lines() raised:", e)

                # Trigger security deposit logic
                order.generate_deposit_invoice(invoice)
        return invoices

    # -------------------------------------------------------------
    #   Generate Security Deposit
    # -------------------------------------------------------------
    def generate_deposit_invoice(self, invoice):
        """
        Add a security deposit line to `invoice` if needed.
        """


        partner = self.partner_id.parent_id or self.partner_id
        if getattr(partner, 'desactivate_security_deposit', False):
            return

        security_deposit_account = self.company_id.security_deposit_account_id
        if not security_deposit_account:
            return

        # Total already paid/recorded deposit for this partner
        security_amount = partner.fetch_partner_paid_deposit(security_deposit_account, ['not_paid', 'paid'])

        # Compute untaxed amount excluding any deposit lines
        lines_for_calc = invoice.invoice_line_ids.filtered(
            lambda l: not l.display_type and 'security deposit' not in (l.name or '').lower()
        )
        amount_untaxed = getattr(invoice, 'amount_untaxed', False) or sum(lines_for_calc.mapped('price_subtotal')) or 0.0
        if not amount_untaxed:
            sign = getattr(invoice, 'direction_sign', 1)
            amount_currency = sum(lines_for_calc.mapped('amount_currency')) or 0.0
            amount_untaxed = sign * amount_currency


        if amount_untaxed < 500:
            return

        rounded_target = math.ceil(amount_untaxed / 500.0) * 500 if amount_untaxed > 0 else 0
        total_needed_deposit = max(rounded_target - amount_untaxed, 0.0)
        new_deposit = total_needed_deposit - (security_amount or 0.0)
        new_deposit = max(new_deposit, 0.0)

        if new_deposit > 0:
            self.create_deposit_invoice_line(invoice, new_deposit, security_deposit_account)


    # -------------------------------------------------------------
    #   Timesheet-based Invoice Generation
    # -------------------------------------------------------------
    def generate_timesheet_invoice(self, timesheet_date):
        """Generate and optionally send timesheet-based invoice."""
        context = dict(self._context)
        context.update({'active_id': self.id, 'open_invoices': True})
        advance_payment_inv = self.env['sale.advance.payment.inv'].with_context(context).create({
            'advance_payment_method': 'delivered',
            'date_end_invoice_timesheet': timesheet_date,
            'invoicing_timesheet_enabled': 1
        })
        invoice_id = advance_payment_inv._create_invoices(self)
        invoice_id.invoice_date = timesheet_date
        if invoice_id:
            if self.invoice_action == 'confirmed':
                invoice_id.action_post()
            elif self.invoice_action == 'confirmed_and_send':
                invoice_id.action_post()
                action = invoice_id.with_context(discard_logo_check=True, is_move_sent=False).action_invoice_sent()
                action.update({'from_auto_invoice': True, 'model': 'account.move', 'rec_id': invoice_id.id})
                self.env['account.move.send.wizard'].with_context(action).create(
                    {'move_id': invoice_id.id}
                ).sudo().action_send_and_print()

    # -------------------------------------------------------------
    #   Timesheet search logic for automatic invoicing
    # -------------------------------------------------------------
    def search_timesheet(self, timesheet_date, sale_line_ids):
        """Search for timesheets before a given date and generate invoice if threshold met."""
        last_invoice = self.env['account.move']
        if self.invoice_ids:
            last_invoice = self.invoice_ids.sorted(key=lambda x: x.create_date, reverse=True)[0]
        if not self.invoice_ids or (last_invoice and last_invoice.invoice_date != timesheet_date):
            domain = [
                ('date', '<=', timesheet_date),
                ('create_date', '<=', timesheet_date),
                ('project_id', '!=', False),
                ('project_id.invoice_for_groupe_riss', '=', False),
                ('validated', '=', True),
                ('timesheet_invoice_id', '=', False),
                ('unit_amount', '>', 0),
                ('so_line', 'in', sale_line_ids.ids)
            ]
            timesheet_ids = self.env['account.analytic.line'].sudo().search(domain)
            if timesheet_ids:
                total_amount = 0.0
                for line in sale_line_ids:
                    total_unit_amount = sum(timesheet_ids.filtered(lambda t: t.so_line == line).mapped('unit_amount'))
                    total_amount += total_unit_amount * line.price_unit
                if total_amount >= self.minimum_amount_invoice:
                    self.generate_timesheet_invoice(timesheet_date)

    # -------------------------------------------------------------
    #   Scheduled automatic timesheet invoicing
    # -------------------------------------------------------------
    def timesheet_invoice_auto_create(self):
        """Automatically generate timesheet invoices based on company policy."""
        today = fields.date.today()
        previous_month = date_utils.subtract(today, months=1)
        domain = [
            ('product_id.service_policy', '=', 'delivered_timesheet'),
            ('order_id.automatically_invoice', 'in', ['activated_last_day_months', 'activated_specific_day']),
            ('invoice_status', '=', 'to invoice')
        ]
        sale_line_ids = self.env['sale.order.line'].sudo().search(domain)
        for order in sale_line_ids.mapped('order_id'):
            if order.automatically_invoice == 'activated_last_day_months':
                timesheet_date = date_utils.end_of(previous_month, "month")
                order.search_timesheet(timesheet_date, sale_line_ids.filtered(lambda sl: sl.order_id.id == order.id))
            if order.automatically_invoice == 'activated_specific_day':
                next_month_date = today + relativedelta(day=1)
                total_days = calendar.monthrange(today.year, today.month)[1]
                if order.day_of_months <= today.day:
                    timesheet_date = today.replace(day=order.day_of_months)
                    order.search_timesheet(timesheet_date, sale_line_ids.filtered(lambda sl: sl.order_id.id == order.id))
                if order.day_of_months > today.day and order.day_of_months <= total_days and not today == next_month_date:
                    date_of_dom = today.replace(day=order.day_of_months)
                    timesheet_date = date_of_dom + relativedelta(months=-1)
                    order.search_timesheet(timesheet_date, sale_line_ids.filtered(lambda sl: sl.order_id.id == order.id))
                if today == next_month_date and (order.day_of_months <= total_days or order.day_of_months > total_days):
                    timesheet_date = date_utils.end_of(previous_month, "month")
                    order.search_timesheet(timesheet_date, sale_line_ids.filtered(lambda sl: sl.order_id.id == order.id))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_price = fields.Float(
        string="Cost",
        compute="_compute_purchase_price",
        digits='Product Price',
        store=True,
        readonly=False,
        groups="base.group_user"
    )

    def _prepare_invoice_line(self, **optional_values):
        """Add product cost to the invoice line values before creation."""
        optional_values.update({'cost': self.purchase_price})
        return super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
