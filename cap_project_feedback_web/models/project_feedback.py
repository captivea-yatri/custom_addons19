# -*- coding: utf-8 -*-
from odoo import models


class ProjectFeedback(models.Model):
    _inherit = 'project.feedback'

    def action_open_feedbacks(self, feedback, project_id):
        action = self.env["ir.actions.actions"]._for_xml_id("cap_project_feedback_web.action_project_feedback_portal")
        action['domain'] = [('id', 'in', feedback.ids)]
        action['context'] = {'default_project_id': project_id.id}
        return action

    def action_read_portal_feedback(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.feedback',
            'res_id': self.id,
            'view_id': self.env.ref('cap_project_feedback_web.feedback_portal_view_form_portal').id,
            'context': {'default_project_id': self.project_id.id}
        }
