# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HrSkillValidator(models.Model):
    _name = 'hr.skill.validator'
    _description = 'Skill Validator Information'

    validator_id = fields.Many2one('res.users', string='Validator')
    domain_skill_id = fields.Many2one('hr.domain.skill', string='Skill Domain')
    companies_ids = fields.Many2many('res.company', string='Company')
