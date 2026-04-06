from odoo import fields, models, api


class TaskValidationStatus(models.Model):
    _name = 'task.validation.status'
    _description = 'Task Validation Status'
    _rec_name = 'session_test_id'

    session_test_id = fields.Many2one(comodel_name='session.test', string='Session', readonly=True)
    task_id = fields.Many2one(comodel_name='project.task', string='Task', readonly=True)
    domain_id = fields.Many2one(related="task_id.project_domain_id", store=True)
    default_domain_id = fields.Many2one(related="task_id.default_domain_id", store=True)
    status = fields.Selection(
        [('to do', 'To Do'), ('failed', 'Failed'), ('success', 'Success'), ('skipped', 'Skipped'),('cancel', 'Cancelled')], default='to do',
        compute="compute_status")
    execution_test_ids = fields.One2many('execution.test', 'task_validation_status_id', string='Execution Tests',
                                         compute="compute_execution_test")
    feedback_ids = fields.One2many('project.feedback', 'task_validation_status_id',
                                   string='Feedbacks')

    def compute_status(self):
        """
        This method is used to set status based on execution test task and session
        """
        for rec in self:
            execution_test_ids = self.env['execution.test'].search(
                [('session_test_id', '=', rec.session_test_id.id), ('task_id', '=', rec.task_id.id)])
            if 'failed' in execution_test_ids.mapped('status'):
                rec.status = 'failed'
            elif 'skipped' in execution_test_ids.mapped('status'):
                rec.status = 'skipped'
            elif 'To do' in execution_test_ids.mapped('status'):
                rec.status = 'to do'
            elif 'cancel' in execution_test_ids.mapped('status'):
                rec.status = 'cancel'
            else:
                rec.status = 'success'

    def compute_execution_test(self):
        """
        This method is used to set execution test based on session test and task
        """
        for rec in self:
            execution_test_ids = self.env['execution.test'].search(
                [('session_test_id', '=', rec.session_test_id.id), ('task_id', '=', rec.task_id.id)])
            rec.execution_test_ids = [(4, execution_test_ids.ids)]

    def write(self, vals):
        """
        This method is used to create feedback and set task , project, phase and employee based on execution test
        """
        recs = super(TaskValidationStatus, self).write(vals)
        for rec in self:
            for feedback_id in rec.feedback_ids:
                feedback_id.write({'project_id': rec.session_test_id.project_id.id,
                                   'phase_id': rec.session_test_id.phase_id.id if rec.session_test_id.phase_id else rec.task_id.default_phase_id.id,
                                   'task_id': rec.task_id.id, 'default_domain_id': rec.default_domain_id.id})
        return recs
