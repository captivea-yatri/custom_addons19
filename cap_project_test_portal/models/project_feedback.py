from odoo import models, fields, _, api


class ProjectFeedback(models.Model):
    _inherit = 'project.feedback'

    test_id = fields.Many2one(comodel_name='test.test', string='Test')
    execution_test_id = fields.Many2one(comodel_name='execution.test', string='Execution Test')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Create a feedback record of execution test if default test is exist
        """
        rec = super(ProjectFeedback, self.sudo()).create(vals_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model and active_model == 'execution.test':
            execution_test = self.env[active_model].browse(active_id)
            if self.env.context.get('default_test_id') and execution_test:
                rec.execution_test_id = execution_test.id
                task_validation_status = execution_test.session_test_id.task_validation_status_ids.filtered(
                    lambda l: execution_test.id in l.execution_test_ids.ids)
                task_validation_status.sudo().write({'feedback_ids' : [(4, rec.id)]})
        partner_list = []
        for feedback in rec:
            if feedback.execution_test_id and feedback.execution_test_id.session_test_id and \
                feedback.execution_test_id.session_test_id.signer_id:
                partner_to_add = feedback.execution_test_id.session_test_id.signer_id.partner_id
                if partner_to_add:
                    partner_list.append(partner_to_add)
            elif feedback.task_validation_status_id and feedback.task_validation_status_id.session_test_id and \
                feedback.task_validation_status_id.session_test_id.signer_id:
                partner_to_add = feedback.task_validation_status_id.session_test_id.signer_id.partner_id
                if partner_to_add:
                    partner_list.append(partner_to_add)
            if partner_list != []:
                feedback._send_invite_for_feedback(partner_ids=partner_list, send_mail=True)
        return rec
