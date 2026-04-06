# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HrSkill(models.Model):
    _inherit = 'hr.skill'

    points = fields.Integer('Points')
    type_of_valivation = fields.Selection(
        [('knowledge_board', 'Knowledge Board'), ('certification', 'Certification'), ('recording', 'Recording')],
        string='Type Of Valivation')
    domain_skill_id = fields.Many2one('hr.domain.skill', string='Domain Skill')
    survey_id = fields.Many2one('survey.survey', string='Survey')




class HrSkillType(models.Model):
    _inherit = 'hr.skill.type'

    is_functional = fields.Boolean(string='Is Functional')
