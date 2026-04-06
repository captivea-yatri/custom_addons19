# -*- coding: utf-8 -*-

from odoo import fields, api, models
from odoo.exceptions import ValidationError


class HrJob(models.Model):
    _inherit = "hr.job"

    minimum_quality_score_required = fields.Float(string = 'Minimum quality score required')
    bonus_tm_target_quality_score_reached = fields.Float(string = 'Bonus for TM When target and quality score reached')
    overtarget_hours_team_manager_criteria = fields.Selection([('targetquality_teammember_reached', 'Target and quality score of team members reached ')])

    @api.constrains('minimum_quality_score_required')
    def minimum_quality_score(self):
        """Ensure quality score stays between 0 and 100."""
        for rec in self:
            if rec.minimum_quality_score_required > 100 or rec.minimum_quality_score_required < 0:
                raise ValidationError(("Quality Score should not greater then 100 and less then Zero"))
