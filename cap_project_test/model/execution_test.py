from odoo import fields, models, api


class ExecutionTest(models.Model):
    _name = 'execution.test'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Execution Test Information'
    _rec_name = 'session_test_id'

    session_test_id = fields.Many2one(comodel_name='session.test', string='Session')
    task_validation_status_id = fields.Many2one(comodel_name='task.validation.status', string='Task Validation Status')
    branch = fields.Text(string='Branch', related='session_test_id.branch', store=True)
    test_id = fields.Many2one(comodel_name='test.test', string='Test')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', related='session_test_id.project_id',
                                 store=True)
    task_id = fields.Many2one(comodel_name='project.task', string='Task', related='test_id.task_id', store=True)
    phase_id = fields.Many2one(comodel_name='project.phase', string='Phase', related='task_id.default_phase_id',
                               store=True)
    domain_id = fields.Many2one(comodel_name='project.domain', related='task_id.project_domain_id',
                                store=True)
    assigned_user_id = fields.Many2one(comodel_name='res.users', string='Assigned User',
                                       related='session_test_id.assigned_user_id', store=True)
    date = fields.Date(string='Date')
    status = fields.Selection(
        [('To do', 'To do'), ('failed', 'Failed'), ('success', 'Success'), ('skipped', 'Skipped'),('cancel', 'Cancelled')],
        default="To do")
    description = fields.Html(string='Description', related="test_id.description", store=True)
    tag_ids = fields.Many2many(comodel_name='project.tags', table_name='test_tag_id', string='Tags')
