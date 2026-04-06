# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SurveyUserInput(models.Model):
    """ Metadata for a set of one user's answers to a particular survey """
    _inherit = "survey.user_input"

    def _compute_scoring_success(self):
        """
               Extend survey scoring computation to update related skill validation requests.

               - Calls the parent method to compute survey success.
               - If the survey is completed ('done'):
                   - Marks the related skill validation request as 'succeed' if passed.
                   - Marks it as 'failed' if not passed.
        """
        res = super(SurveyUserInput, self)._compute_scoring_success()
        for user_input in self:
            skill_req_id = self.env['hr.skill.validation.request'].search(
                [('survey_user_input_id', '=', user_input.id)])
            if user_input.state == 'done' and skill_req_id.status not in ['succeed', 'failed']:
                if user_input.scoring_success:
                    skill_req_id.action_success()
                else:
                    skill_req_id.action_failed()
        return res
