# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    """
     There is on field add in product template its get default currency from the company.
    """

    def _get_default_currency_id(self):
        try:
            main_company = self.sudo().env.ref('base.main_company')
        except ValueError:
            main_company = self.env['res.company'].sudo().search([], limit=1, order="id")
        return self.company_id.sudo().currency_id.id or main_company.currency_id.id

    bom_currency_id = fields.Many2one('res.currency', default=_get_default_currency_id, string="Currency (BOM)")
