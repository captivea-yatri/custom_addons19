from odoo import models, fields, api


class Survey(models.Model):
    _inherit = 'survey.survey'

    skill_validation_request_ids = fields.One2many('hr.skill', 'survey_id', string="Skill Validation Request")
