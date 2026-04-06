# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    partner_id = fields.Many2one('res.partner', groups="hr.group_hr_user", string="Partner")
    # github_name = fields.Char(string="Github name", groups="hr.group_hr_user")
    x_studio_joining_date = fields.Date('Joining Date', groups="hr.group_hr_user")
    medical_visit_date = fields.Date('Medical Visit', groups="hr.group_hr_user")
