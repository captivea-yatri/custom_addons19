from odoo import fields, models, api, _


class Test(models.Model):
    _inherit = 'test.test'

    def action_feedback(self):
        return {
            'name': _("Feedback"),
            'view_mode': 'list, form',
            'view_id': False,
            'res_model': 'project.feedback',
            'type': 'ir.actions.act_window',
            'domain': [('test_id', '=', self.id)],
            'context': {'default_test_id': self.id},
            'views': [(self.env.ref('cap_project_feedback.new_project_feedback_view_tree_id').id, 'list'),
                      (self.env.ref('cap_project_feedback.new_project_feedback_form_view_id').id, 'form')],
        }
