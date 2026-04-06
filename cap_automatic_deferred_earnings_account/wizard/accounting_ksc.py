from odoo import models, fields, api


class accountingksc(models.TransientModel):
    _inherit = "account.payment.register"

    description = fields.Text(string="Please Provide details here: ")
