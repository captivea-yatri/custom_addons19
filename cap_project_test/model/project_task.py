from odoo import fields, models, api


class ProjectTask(models.Model):
    _inherit = 'project.task'

    tests_ids = fields.One2many(comodel_name='test.test', inverse_name='task_id', string='Tests')
    staging_branch_to_use = fields.Text(string='Staging branch to use')
    last_task_validation_status = fields.Selection(
        [('to do', 'To Do'), ('failed', 'Failed'), ('success', 'Success'), ('skipped', 'Skipped'),('cancel', 'Cancelled')],
        string='Test Status',
        compute='compute_last_task_validation_status_and_date')
    last_task_validation_status_date = fields.Date(string="Test Date",
                                                   compute='compute_last_task_validation_status_and_date')

    def compute_last_task_validation_status_and_date(self):
        """
        This method is used to set last task validation status and last task validation status date based on task
        validation status
        """
        for rec in self:
            task_validation_status_id = self.env['task.validation.status'].search([('task_id', '=', rec.id)], limit=1,
                                                                                  order='id desc')
            rec.last_task_validation_status = task_validation_status_id.status
            rec.last_task_validation_status_date = task_validation_status_id.session_test_id.date

    def action_task_execution_test_object(self):
        """
        This function is used to open execution test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_execution_test')
        action['domain'] = [('task_id', '=', self.id)]
        return action

    def action_task_validation_status(self):
        """
        This function is used to open task validation status view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_task_validation_status')
        action['domain'] = [('task_id', '=', self.id)]
        action['context'] = {'create': False}
        return action

    def action_session_test_object(self):
        """
        This function is used to open session test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_session_test')
        action['domain'] = [('project_id', '=', self.project_id.id), ('task_ids', '=', self.ids)]
        action['context'] = {'default_project_id': self.project_id.id, 'default_task_ids': self.ids}
        return action
