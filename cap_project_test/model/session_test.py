from odoo import fields, models, api, _
from datetime import datetime


class SessionTest(models.Model):
    _name = 'session.test'
    _description = 'Session Test'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    date = fields.Date(string='Date', default=fields.Datetime.now, copy=False)
    branch = fields.Text(string='Branch')
    assigned_user_id = fields.Many2one(comodel_name='res.users', string='Assigned User', required=True,
                                       domain="[('id', 'in', assigned_user_ids)]")
    project_id = fields.Many2one(comodel_name='project.project', string='Project', required=True)
    phase_id = fields.Many2one(comodel_name='project.phase', string='Phase')

    domain_ids = fields.Many2many(comodel_name='default.domain', table_name='test_default_domain_table',
                                  string='Domains')
    task_ids = fields.Many2many(comodel_name='project.task', table_name='test_project_task_tabel', string='Tasks',
                                domain="[('project_id', '=', project_id)]")
    status = fields.Selection([('draft', 'Draft'),('sent','Sent'),('in progress','In Progress'), ('closed', 'Closed'), ('signed', 'Signed'),('cancel', 'Cancelled')], default='draft',
                              readonly=True, copy=False, tracking=True)
    pick_only = fields.Selection(
        [('all', 'All'), ('failed_last_time', 'Tests that Failed Last Time'),
         ('skipped_last_time', 'Tests that Failed Last Time or Skipped')], default="all", copy=False)
    no_of_success_execution_test_object = fields.Integer(string='Number Of Success Execution Tests',
                                                         compute="compute_execution_test_based_on_status")
    no_of_failed_execution_test_object = fields.Integer(string='Number Of Failed Execution Tests',
                                                        compute="compute_execution_test_based_on_status")
    no_of_skipped_execution_test_object = fields.Integer(string='Number Of Skipped Execution Tests',
                                                         compute="compute_execution_test_based_on_status")
    no_of_todo_execution_test_object = fields.Integer(string='Number Of Todo Execution Tests',
                                                      compute="compute_execution_test_based_on_status")
    total_no_of_execution = fields.Integer(string='Total Number Of Execution Tests',
                                           compute="compute_execution_test_based_on_status")
    hide_the_initialize_button = fields.Boolean("Hide button of initialize test if once we click on it", copy=False)
    execution_test_ids = fields.One2many('execution.test', 'session_test_id', string='Execution Tests', readonly=True)
    task_validation_status_ids = fields.One2many('task.validation.status', 'session_test_id',
                                                 string='Task Validation Status')
    attachment_id = fields.Many2one('ir.attachment', auto_join=True, copy=False, readonly=True)
    file = fields.Binary('File', related="attachment_id.datas")
    file_name = fields.Char("File Name", readonly=True, related='attachment_id.name')
    signer_id = fields.Many2one('res.users', string="Signatory", help="send customer for sign the pdf", copy=False,
                                domain=lambda self: [('groups_id', 'in',
                                                      [self.env.ref('base.group_user').id,
                                                       self.env.ref('base.group_portal').id])])
    assigned_user_ids = fields.Many2many('res.users', string="Assigned Users", copy=False,
                                         compute="compute_user_to_get_project_followers", store=True)
    tag_ids = fields.Many2many(comodel_name='project.tags', table_name='session_test_tag_id', string='Tags')
    message = fields.Html(string='Message')

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(SessionTest, self).create(vals_list)
    #     for rec in res:
    #         if rec.project_id:
    #             pm_of_customer = rec.project_id.signatory_progress_report_partner_id
    #             if pm_of_customer:
    #                 rec._send_invite_for_test(partner_ids=pm_of_customer, send_mail=True)
    #     return res

    def _send_invite_for_test(self, partner_ids, send_mail):
        if partner_ids:
            invite_wizard = self.env['mail.wizard.invite'].sudo().create({
                'res_model': 'session.test',
                'res_id': self.id,
                'partner_ids': [(4, partner_id.id) for partner_id in partner_ids],
                'message': _('You have been invited to follow this Session Test: %s') % self.name,
                'notify': send_mail,
            })
            invite_wizard.sudo().add_followers()


    def cancel_execution_test(self):
        self.write({'status': 'cancel'})
        self.execution_test_ids.status = 'cancel'
        self.task_validation_status_ids.status = 'cancel'


    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        result['date'] = datetime.now()
        return result

    @api.onchange('assigned_user_id')
    def _onchange_assigned_user_id(self):
        for rec in self:
            if rec.assigned_user_id:
                rec.signer_id = rec.assigned_user_id

    @api.depends('project_id')
    def compute_user_to_get_project_followers(self):
        """
        This method is used for set internal users or project followers into assigned user ids and visible into assigned user id field
        """
        for rec in self:
            current_user = self.env.user
            final_user_ids = []

            if current_user.share:
                if rec.project_id:
                    partner_user_ids = (
                            rec.project_id.partner_id.child_ids.user_ids.ids +
                            rec.project_id.partner_id.user_ids.ids
                    )
                    message_user_ids = (
                            rec.project_id.message_partner_ids.user_ids.ids
                            or rec.project_id.message_partner_ids.user_id.ids
                    )
                    user_ids = partner_user_ids + message_user_ids

                    portal_users = self.env['res.users'].search([
                        ('id', 'in', user_ids),
                        ('share', '=', True)
                    ])
                    final_user_ids = portal_users.ids

            elif current_user.has_group('base.group_user'):
                internal_users = self.env['res.users'].search([
                    ('groups_id', '=', self.env.ref('base.group_user').id)
                ])
                final_user_ids = internal_users.ids

                if rec.project_id:
                    partner_user_ids = (
                            rec.project_id.partner_id.child_ids.user_ids.ids +
                            rec.project_id.partner_id.user_ids.ids
                    )
                    message_user_ids = (
                            rec.project_id.message_partner_ids.user_ids.ids
                            or rec.project_id.message_partner_ids.user_id.ids
                    )
                    final_user_ids += partner_user_ids + message_user_ids

            if final_user_ids:
                rec.write({'assigned_user_ids': [(6, 0, list(set(final_user_ids)))]})

    def compute_execution_test_based_on_status(self):
        """
        This method is used to compute number of execution test based on execution status
        """
        for rec in self:
            execution_test_ids = self.env['execution.test']
            rec.no_of_success_execution_test_object = len(
                execution_test_ids.search([('session_test_id', '=', rec.id), ('status', '=', 'success')]))
            rec.no_of_failed_execution_test_object = len(
                execution_test_ids.search([('session_test_id', '=', rec.id), ('status', '=', 'failed')]))
            rec.no_of_skipped_execution_test_object = len(
                execution_test_ids.search([('session_test_id', '=', rec.id), ('status', '=', 'skipped')]))
            rec.no_of_todo_execution_test_object = len(
                execution_test_ids.search([('session_test_id', '=', rec.id), ('status', '=', 'To do')]))
            rec.total_no_of_execution = len(execution_test_ids.search([('session_test_id', '=', rec.id)]))

    def action_create_execution_test(self):
        """
        This method is used to create execution test based on task and status
        - Pick only = ALL then create all execution test based on phase, project, domain and task
        - Pick only = failed then create all Failed execution test based on phase, project, domain and task
        - Pick only = Skipped then create all skipped execution test based on task, phase , domain and project
        """
        self.hide_the_initialize_button = True
        test_ids = self.find_test_based_on_criteria()
        for test_id in test_ids:
            if self.pick_only == 'all':
                self.create_execution_test(test_id, test_id.project_domain_id)
                self.create_task_validation_status(test_id.task_id)
            if self.pick_only == 'failed_last_time':
                if test_id and test_id.status_of_last_execution_test not in ['success', False]:
                    execution_test_ids = self.find_execution_test(test_id, test_id.task_id, test_id.project_domain_id,
                                                                  ['failed'])
                    if execution_test_ids:
                        for execution_test_id in execution_test_ids:
                            if execution_test_id.session_test_id.status in ['closed', 'signed']:
                                self.create_execution_test(execution_test_id.test_id, test_id.project_domain_id)
                                self.create_task_validation_status(test_id.task_id)
            if self.pick_only == 'skipped_last_time':
                if test_id and test_id.status_of_last_execution_test != 'success':
                    execution_test_ids = self.find_execution_test(test_id, test_id.task_id, test_id.project_domain_id,
                                                                  ['skipped', 'failed'])
                    if execution_test_ids:
                        for execution_test_id in execution_test_ids:
                            if execution_test_id.session_test_id.status in ['closed', 'signed']:
                                self.create_execution_test(execution_test_id.test_id, test_id.project_domain_id)
                                self.create_task_validation_status(test_id.task_id)

    def find_test_based_on_criteria(self):
        """
        This method is used to find the test based on project , domain and task phase
        """
        domain = [('project_id', '=', self.project_id.id)]
        if self.domain_ids:
            domain += [('project_domain_id.default_domain_id', 'in', self.domain_ids.ids)]
        if self.phase_id:
            domain += [('task_id.default_phase_id', '=', self.phase_id.id)]
        if self.task_ids:
            domain += [('task_id', 'in', self.task_ids.ids)]
        if self.tag_ids:
            domain += [('tag_ids','in',self.tag_ids.ids)]
        test_ids = self.env['test.test'].search(domain)
        return test_ids

    def find_execution_test(self, test_id, task_id, domain_id, status):
        """
        This method is used to find execution test based on project, phase, task, domain, status
        """
        execution_test_ids = self.env['execution.test'].search(
            [('test_id', '=', test_id.id),
             ('project_id', '=', self.project_id.id), ('test_id.template_test_id', '=', test_id.template_test_id.id),
             ('status', 'in', status)
             ], limit=1, order='id desc')
        return execution_test_ids

    def create_execution_test(self, test_id, domain_id):
        """
        This method is used to create execution test record
        """
        self.env['execution.test'].create({
            'session_test_id': self.id,
            'branch': self.branch,
            # 'date': self.date,
            'project_id': self.project_id.id,
            'task_id': test_id.task_id.id,
            'assigned_user_id': self.assigned_user_id.id,
            'phase_id': self.phase_id.id,
            'domain_id': domain_id.id,
            'test_id': test_id.id,
            'tag_ids': test_id.tag_ids.ids
        })

    def create_task_validation_status(self, task_id):
        """
        This method is used to create task validation status record
        """
        task_validation_status_id = self.env['task.validation.status'].search([('session_test_id', '=', self.id),
                                                                               ('task_id', '=', task_id.id)])
        if not task_validation_status_id:
            self.env['task.validation.status'].create({
                'session_test_id': self.id,
                'task_id': task_id.id,
            })

    def action_execution_test(self):
        """
        This method is used to open execution test list view records
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_execution_test')
        action['domain'] = [('session_test_id', '=', self.id)]
        action['context'] = {'create': False, 'delete': False, 'edit': False}
        return action

    def action_task_validation_status(self):
        """
        This method is used to open task validation status list view records
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_task_validation_status')
        action['domain'] = [('session_test_id', '=', self.id)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def action_close_the_session(self):
        execution_test_ids = self.env['execution.test'].search(
            [('session_test_id', '=', self.id), ('status', '=', 'To do')])
        for execution_test_id in execution_test_ids:
            execution_test_id.status = 'skipped'
            execution_test_id.date = datetime.now()
        self.status = 'closed'
        if not self.date:
            self.date = datetime.now()

    def session_test_message_auto_subscribe_notify(self):
        """
        This method is used to send mail to the assigned user
        """
        if self.status == 'draft':
            self.status = 'sent'
        template_id = self.env['ir.model.data']._xmlid_to_res_id(
            'cap_project_test.mail_template_for_session_test',
            raise_if_not_found=False)
        if not template_id:
            return

        values = {
            'object': self,
        }
        values.update(assignee_name=self.assigned_user_id.sudo().name)
        assignation_msg = self.env['ir.qweb']._render('cap_project_test.mail_template_for_session_test', values,
                                                      minimal_qcontext=True)

        message_body = assignation_msg
        template_obj = self.env['mail.mail']
        template_data = {
            'subject': _('You have been assigned to %s', self.name),
            'body_html': message_body,
            'email_to': self.assigned_user_id.sudo().partner_id.email
        }
        template_id = template_obj.sudo().create(template_data)
        template_obj.send(template_id)
        template_id.send()
        self.sudo().message_post(body=message_body)

