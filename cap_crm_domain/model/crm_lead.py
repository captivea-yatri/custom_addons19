# -*- coding: utf-8 -*-
from odoo import fields, models, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    interested_domain_ids = fields.Many2many('default.domain', 'crm_domain_rel', 'crm_id', 'domain_id',
                                             string="Interested Domain")
