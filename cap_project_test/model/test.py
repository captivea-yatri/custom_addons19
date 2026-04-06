from odoo import fields, models, api


class Test(models.Model):
    _name = 'test.test'
    _description = 'Ksc Test Information'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    template_test_id = fields.Many2one(comodel_name='template.test', string='Template Test')
    task_id = fields.Many2one(comodel_name='project.task', string='Task', ondelete='cascade', required=True)
    project_domain_id = fields.Many2one(comodel_name='project.domain', related='task_id.project_domain_id', store=True,
                                        string='Default Domain')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', related='task_id.project_id',
                                 store=True)
    tag_ids = fields.Many2many(comodel_name='project.tags', table_name='test_tag_id', string='Tags')
    description = fields.Html(string='Description')
    status_of_last_execution_test = fields.Selection([('failed', 'Failed'), ('success', 'Success')],
                                                     string='Status of Last Execution Test',
                                                     compute='compute_status_date_based_on_last_execution_test')
    date_of_last_execution_test = fields.Date(string='Date Of Last Execution Test',
                                              compute='compute_status_date_based_on_last_execution_test')
    assigned_user_id = fields.Many2one(comodel_name='res.users',
                                       compute='compute_status_date_based_on_last_execution_test',
                                       string='Assigned User of last Execution Test')
    stage_id = fields.Many2one(comodel_name="project.task.type", readonly=False)
    active = fields.Boolean(default=True)

    def compute_status_date_based_on_last_execution_test(self):
        """
        This method is used to set date_of_last_execution_test, assigned_user_id and status_of_last_execution_test
        based on last execution status, date and assigned user
        """
        for rec in self:
            execution_test_id = self.env['execution.test'].search(
                [('test_id.template_test_id', '=', rec.template_test_id.id), ('test_id', '=', rec.id),
                 ('status', '!=', 'cancel')], limit=1,order='id desc')
            if execution_test_id.status == 'failed':
                rec.status_of_last_execution_test = 'failed'
            elif execution_test_id.status == 'success':
                rec.status_of_last_execution_test = 'success'
            else:
                rec.status_of_last_execution_test = False
            rec.date_of_last_execution_test = execution_test_id.date
            rec.assigned_user_id = execution_test_id.assigned_user_id

    def action_execution_test_object(self):
        """
        This function is used to open execution test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_execution_test')
        action['domain'] = [('test_id', '=', self.id)]
        return action


