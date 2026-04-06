# -*- coding: utf-8 -*-


from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.company'

    glcr_steps = fields.Selection([('1', '1 Step'), ('2', '2 Step')], string='Go Live Change Request Steps')
    glcr_s2_validater = fields.Many2one('res.users', 'Step 2 Validater')
