from odoo import api, fields, models


class SurveyInvite(models.TransientModel):
    _inherit = 'survey.invite'

    def _prepare_answers(self, partners, emails):
        answer = super(SurveyInvite, self)._prepare_answers(partners, emails)
        context = self.env.context
        if context.get('skill_request_id', False):
            request_id = self.env['hr.skill.validation.request'].browse(context.get('skill_request_id'))
            if request_id:
                request_id.survey_user_input_id = answer.id
        return answer
