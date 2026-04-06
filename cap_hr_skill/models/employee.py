# -*- coding: utf-8 -*-

from odoo import fields, models, api


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    functional_knowledge_score = fields.Integer(string='Functional Knowledge Score',
                                                compute='_compute_functional_and_global_knowledge_score')
    global_knowledge_score = fields.Integer(string='Global Knowledge Score',
                                            compute='_compute_functional_and_global_knowledge_score')

    @api.depends('employee_skill_ids.skill_type_id.is_functional', 'employee_skill_ids.skill_id.points')
    def _compute_functional_and_global_knowledge_score(self):
        """
                Compute functional and global knowledge scores for each employee.

                Functional score: sum of points for functional skill types.
                Global score: sum of points for all employee skills.
                """
        for employee in self:
            functional_skills = employee.employee_skill_ids.filtered(
                lambda skill: skill.skill_type_id.is_functional
            )
            employee.functional_knowledge_score = functional_skills and sum(
                functional_skills.skill_id.mapped('points')) or 0
            skill_points = sum(employee.skill_ids.mapped('points'))
            employee.global_knowledge_score = skill_points
