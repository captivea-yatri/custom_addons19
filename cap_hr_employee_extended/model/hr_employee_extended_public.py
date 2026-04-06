# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HrEmployeeExtendedPublic(models.Model):
    _inherit = 'hr.employee.public'

    functional_knowledge_score = fields.Integer(string='Functional Knowledge Score',
                                                related="employee_id.functional_knowledge_score")
    global_knowledge_score = fields.Integer(string='Global Knowledge Score',
                                            related="employee_id.global_knowledge_score")
