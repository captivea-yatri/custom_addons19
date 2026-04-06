from odoo import fields, models, api
from datetime import datetime


class ExecutionTest(models.Model):
    _inherit = 'execution.test'

    is_session_test_draft = fields.Boolean(string="Mark button_invisible", compute="_compute_is_session_test_draft",
                                           default=True)
    feedback_ids = fields.One2many('project.feedback', 'execution_test_id',
                                   string='Feedbacks')

    def set_status_success(self):
        """
        This method is used to set success state of execution test while button click
        """
        self.status = 'success'
        self.date = datetime.now()

    def set_status_skip(self):
        """
        This method is used to set skip state of execution test while button click
        """
        self.status = 'skipped'
        self.date = datetime.now()

    def set_status_failed(self):
        """
        This method is used to set fail state of execution test while button click
        """
        self.status = 'failed'
        self.date = datetime.now()
        return {
            'name': 'Feedback',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'project.feedback',
            'view_id': self.env.ref('cap_project_test_portal.feedback_portal_view_form').id,
            'context': {'default_test_id': self.test_id.id, 'default_project_id': self.project_id.id}
        }

    def set_status_Todo(self):
        self.status = 'To do'
        self.date = datetime.now()

    def _compute_is_session_test_draft(self):
        """
        This method is used to set feedback readonly while session test state is in close or signed
        """
        for rec in self:
            rec.is_session_test_draft = True if rec.session_test_id.status in ['draft', 'in progress'] and rec.session_test_id.assigned_user_id.id == self.env.user.id else False
