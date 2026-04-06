# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    revenue_enquiry_user_id = fields.Many2one('res.users', 'Revenue Enquiry User')
    closing_so_user_id = fields.Many2one('res.users', 'User Closing Sale Order')
    res_company_time_credit_config_ids = fields.One2many('res.company.time.credit.config', 'company_id', string="Time Credit Config")
    number_of_months_after_credit_time_expires = fields.Integer(string='Months after credit time expires')

    @api.constrains('number_of_months_after_credit_time_expires')
    def _check_positive_number_of_months(self):
        ''' Ensure that number_of_months_after_credit_time_expires is greater than 0 '''
        for record in self:
            if record.number_of_months_after_credit_time_expires < 0:
                raise ValidationError(_('The value for Time Credit Expiry Months must be greater than 0 !'))