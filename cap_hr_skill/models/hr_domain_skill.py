# -*- coding: utf-8 -*-

from odoo import fields, models, api


class HrDomainSkill(models.Model):
    _name = 'hr.domain.skill'
    _description = 'Domain Skill'
    name = fields.Char("Name")
    skill_type_id = fields.Many2one('hr.skill.type', string="Skill Type")

