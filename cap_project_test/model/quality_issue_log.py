from odoo import api, fields, models


class QualityIssueLog(models.Model):
    _inherit = "quality.issue.log"

    feedback_id = fields.Many2one("project.feedback", string="Feedback")
