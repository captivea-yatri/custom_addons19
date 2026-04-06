# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Project(models.Model):
    _inherit = "project.project"

    def remove_unused_project_domain(self, project_requirement_ids, req_project_domain_ids=[]):
        feedback_domain_ids = self.env['project.feedback'].search(
            [('project_id', '=', self.id), ('phase_id', '!=', False), ('domain_id', '!=', False)]).mapped('domain_id')
        req_project_domain_ids += feedback_domain_ids.ids
        return super(Project, self).remove_unused_project_domain(project_requirement_ids, req_project_domain_ids)

    def action_feedback(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cap_project_feedback.my_project_feedback_action_detail")
        if action:
            action['view_ids'] = [(self.env.ref('cap_project_feedback.new_project_feedback_form_view_id').id, 'form'),
                                  (self.env.ref('cap_project_feedback.new_project_feedback_view_tree_id').id, 'list')],
            action['domain'] = [('project_id', '=', self.id)]
            action['context'] = {'default_project_id': self.id}
        return action

    def action_view_feedback_project(self):
        action = self.env["ir.actions.actions"]._for_xml_id("cap_project_feedback.my_project_feedback_action_detail")
        if action:
            action['view_ids'] = [(self.env.ref('cap_project_feedback.new_project_feedback_form_view_id').id, 'form'),
                                  (self.env.ref('cap_project_feedback.new_project_feedback_view_tree_id').id, 'list')],
            action['domain'] = [('project_id', '=', self.id)]
            action['context'] = {'default_project_id': self.id}
        return action
