# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model_create_multi
    def create(self, vals_list):
        """Restricting users to set partners that are company in lead"""
        partner_company = self.env['res.company'].search([('partner_id', '!=', False)]).mapped('partner_id')
        for vals in vals_list:
            if 'partner_id' in vals and vals['partner_id'] in partner_company.ids:
                raise ValidationError('Partners cannot be assigned to opportunities that are associated with our internal companies!')
        return super(CrmLead, self).create(vals_list)