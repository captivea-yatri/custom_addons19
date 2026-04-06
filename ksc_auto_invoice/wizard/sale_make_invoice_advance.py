# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoices(self, sale_orders):
        """
           Extends invoice creation to automatically include a
           security deposit line for delivered-timesheet products
           if the customer has security deposit enabled.
        """
        context = dict(self._context)
        invoice_ids = super(SaleAdvancePaymentInv, self.with_context(timesheet_validation=True))._create_invoices(sale_orders)
        if self.advance_payment_method == 'delivered' and not context.get('skip_security_deposit', False):
            for invoice in invoice_ids:
                partner_id = invoice.partner_id
                partner_id = partner_id.parent_id or partner_id
                order_line_ids = invoice.invoice_line_ids.mapped('sale_line_ids')
                if (not partner_id.desactivate_security_deposit and
                        order_line_ids.filtered(lambda l: l.product_id.service_policy == 'delivered_timesheet')):
                    order_id = order_line_ids.mapped('order_id')
                    order_id.generate_deposit_invoice(invoice)
        return invoice_ids

    def create_invoices(self):
        """
            Wrapper around standard invoice creation with
            timesheet validation context enabled.
        """
        invoice_ids = super(SaleAdvancePaymentInv, self.with_context(timesheet_validation=True)).create_invoices()
        return invoice_ids

