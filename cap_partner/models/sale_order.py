# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    quotation_sent_date = fields.Date('Quotation Sent On')
    display_maintenance_support_terms = fields.Boolean(string='Display Maintenance Support Terms', tracking=True)

    def write(self, vals):
        """Automatically set quotation_sent_date when the order state becomes 'sent'."""
        if vals.get('state', False) and vals.get('state') == 'sent':
            vals.update({'quotation_sent_date': fields.Date.today()})
        return super(SaleOrder, self).write(vals)

    def _prepare_invoice(self):
        """Prepare invoice values by removing narration and applying partner-specific bank account."""
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        del invoice_vals['narration']
        if self.partner_id.property_company_bank_account_id:
            invoice_vals.update({'partner_bank_id': self.partner_id.property_company_bank_account_id.id})
        return invoice_vals
