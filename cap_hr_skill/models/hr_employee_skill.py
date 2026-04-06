# -*- coding: utf-8 -*-
from email.policy import default

from odoo import fields, models, api


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee.skill'

    skill_date = fields.Date('Skill Date',default=fields.Date.today, copy=False)