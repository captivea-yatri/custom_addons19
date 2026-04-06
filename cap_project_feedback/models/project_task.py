# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError

PROJECT_TASK_READABLE_FIELDS = {
    'feedback_ids',
    'default_domain_ids',
    'default_domain_id',
    'estimate_time',
    'id',
    'task_url'
}

PROJECT_TASK_WRITABLE_FIELDS = {
    'feedback_ids',
    'description',
    'default_domain_id',
    'default_domain_ids',
    'estimate_time',
    'id',
    'task_url'
}


class ProjectTask(models.Model):
    _inherit = 'project.task'

    feedback_ids = fields.One2many('project.feedback', 'task_id', string='Feedback')
    estimate_time = fields.Float(related="project_requirement_id.estimate_time", store=True)

    task_url = fields.Char('URL',compute="_get_task_url",compute_sudo=True)

    def _get_task_url(self):
        for rec in self:
            rec.task_url = rec.get_base_url() + rec.get_portal_url()

    @property
    def SELF_READABLE_FIELDS(self):
        """
        This method is used to add read access of feedback field to portal user
        """
        return super().SELF_READABLE_FIELDS | PROJECT_TASK_READABLE_FIELDS

    @property
    def SELF_WRITABLE_FIELDS(self):
        """
        This method is used to add write access of feedback field to portal user
        """
        return super().SELF_WRITABLE_FIELDS | PROJECT_TASK_WRITABLE_FIELDS

    def access_feedback_list(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("cap_project_feedback.my_project_feedback_action_detail")
        if action:
            action['view_ids'] = [(self.env.ref('cap_project_feedback.new_project_feedback_form_view_id').id, 'form'),
                                  (self.env.ref('cap_project_feedback.new_project_feedback_view_tree_id').id, 'tree')],
            action['domain'] = [('task_id', '=', self.id)]
            action['context'] = {'default_project_id': self.project_id.id, 'default_task_id': self.id,
                                 'default_domain_id': self.project_domain_id.id,
                                 'default_default_domain_id': self.default_domain_id.id,
                                 'default_phase_id': self.default_phase_id.id}
        return action

    def write(self, vals):
        if self.env.user.has_group('base.group_portal'):
            if 'description' in vals:
                raise UserError(_('Sorry! Description update is restricted'))
        return super(ProjectTask, self).write(vals)
