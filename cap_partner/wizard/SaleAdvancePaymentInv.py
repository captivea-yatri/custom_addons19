# coding: utf-8
from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, so_line, accounts):
        """Add partner-specific bank account to invoice values from partner's bank accounts"""
        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, so_line, accounts)
        if order.partner_id.property_company_bank_account_id:
            invoice_vals.update({'partner_bank_id': order.partner_id.property_company_bank_account_id.id})
        return invoice_vals
