from odoo import fields, models, api, _


class TaskValidationStatus(models.Model):
    _inherit = 'task.validation.status'

    mark_feedback_as_readonly = fields.Boolean(string="Mark Feedback As Readonly", compute="_compute_feedback_readonly",
                                               store=True, default=False)
    feedback_readonly = fields.Boolean(string="Mark Feedback As Readonly", compute="mark_feedback_read_only",
                                       default=True)

    def action_open_execution_test(self):
        return {
            'name': 'Execution Test',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'execution.test',
            'context': {'create': False, 'delete': False},
            'views': [(self.env.ref('cap_project_test_portal.execution_test_portal_list').id, 'tree'),
                      (self.env.ref('cap_project_test_portal.execution_test_portal_form').id, 'form')],
            'domain': [('id', 'in', self.execution_test_ids.ids)],
        }

    @api.depends('session_test_id.status')
    def _compute_feedback_readonly(self):
        """
        This method is used to set feedback readonly while session test state is in close or signed
        """
        for rec in self:
            rec.mark_feedback_as_readonly = True if rec.session_test_id.status in ['closed',
                                                                                   'signed'] else False

    def mark_feedback_read_only(self):
        for rec in self:
            if rec.session_test_id.assigned_user_id.id == self.env.user.id:
                rec.feedback_readonly = False
            else:
                rec.feedback_readonly = True
