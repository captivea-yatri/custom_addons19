# coding: utf-8
from odoo import _, api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    security_deposit_account_id = fields.Many2one('account.account',string="Security Deposit account")
