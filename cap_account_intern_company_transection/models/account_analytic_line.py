# coding: utf-8
from odoo import _, api, fields, models


class AccountAnalytic(models.Model):
    _inherit = 'account.analytic.line'

    subsidiary_invoice_id = fields.Many2one('account.move', string='Subsidiary Invoice Id')