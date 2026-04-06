from odoo import api, fields, models, Command, SUPERUSER_ID
from datetime import datetime,timedelta, date
from odoo.exceptions import ValidationError
import base64
from werkzeug.urls import url_join, url_quote
from odoo.tools import config, get_lang, is_html_empty, formataddr, groupby, format_date
from odoo.tools.float_utils import float_round

#TODO : need to verify field used in code planned hours and also functionality

class ProjectProgress(models.Model):
    _name = 'project.progress'
    _description = 'Project Progress Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(related="project_id.name")
    project_id = fields.Many2one("project.project", string="Project", tracking=True)
    status = fields.Selection([('draft','Draft'),('sent','Sent'),('signed','Signed')],string='Status',default='draft',copy=False)
    global_progress = fields.Float("Global Progress", store=True,
                                   help="Delivered progression, how Captivea delivered the hours for the project, maintaining a small gap between this and the Project progress is a good practice to secure the project. The higher the gap, the higher the risk is to have lots of feedbacks")
    validation_progress = fields.Float("Validation Progress", store=True,
                                       help="Customer feeling of what he was able to test and validate (time of tasks to push in prod, to validate in prod and in prod / total time)")
    out_of_scope_included_in_current_phase = fields.Float("Out of Scope Included in Current Phase", store=True,
                                                          help="Sum of out of scope tasks (tasks not planned in the requirement list) We display the sum so the customer keep in mind the whole amount validated")
    remaining_hours = fields.Float("Remaining Hours to Go Live", readonly=False, store=True,
                                   help="Sum of hours to go live for the project(Allocated hours - Hours spent) for not validated task")
    left_hours = fields.Float("Hours Left In Current Bucket", compute="_get_left_progress", store=True,
                              help="Total remaining quantity of project's sales order lines")
    go_live_date = fields.Date("Go Live Date", related="project_id.x_studio_go_live_date")
    milestone_history_ids = fields.One2many("project.milestone.history", "project_progress_id", readonly=False)
    hold_task_ids = fields.Many2many("project.task", "project_progress_task_hold_rel", "progress_report_id", "task_id",
                                     string="Task On Hold")
    future_task_ids = fields.Many2many("project.task", "project_progress_task_rel", "progress_report_id", "task_id",
                                       string="Future Tasks")
    demo_meeting_task = fields.Html("Demo Meeting Tasks")
    sale_order_line_ids = fields.Many2many("sale.order.line", "progress_so_line_ids", "progress_report_id",
                                           "so_line_id", string="Sale order Lines")
    notes = fields.Text("Notes")
    message = fields.Html("Notes")
    days = fields.Integer("Days")
    last_report = fields.Boolean("Last Report", compute="_get_last_report", store=True)
    company_id = fields.Many2one('res.company', related='project_id.company_id', store=True)
    phase_id = fields.Many2one(comodel_name='project.phase', string='Phase',
                               domain="[('project_id', '=', project_id)]", tracking=True)
    project_domain_history_ids = fields.One2many('project.domain.history', 'project_progress_id',domain=['|','|',('estimated_time', '!=', 0.0),('task_estimated_time', '!=', 0.0),('task_passed_time', '!=', 0.0)],
                                                 string='Project Domain History', store=True)
    signatory_progress_report_partner_id = fields.Many2one('res.partner', required=True,
                                                           string="Signatory Project Progress Report")
    signatory_portal_report_partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids')
    cc_progress_report_user_ids = fields.Many2many('res.users', 'rel_progress_user_res_users',
                                                   'user_id', 'progress_report_id',
                                                   string="CC Project Progress Report",
                                                   domain=lambda self: [('groups_id', 'in',
                                                                         [self.env.ref(
                                                                             'base.group_user').id,
                                                                          self.env.ref(
                                                                              'base.group_portal').id])])
    cc_progress_report_partner_ids = fields.Many2many('res.partner', 'res_partner_refe', 'partner_id',
                                                      'progress_report_id',
                                                      string="CC Project Progress Report")
    cc_progress_report_internal_partner_partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids')
    sign_request_ids = fields.One2many('sign.request', 'project_progress_id', readonly=True)
    past_done_task_history_ids = fields.One2many('task.history.log', 'progress_report_id')
    project_status_id = fields.Many2one('project.status', related="project_id.project_status_id")
    project_progress_template = fields.Selection(
        [('project_progress_with_deadline', 'Project Progress Report with Deadline'),
         ('project_progress_no_deadline', 'Project Progress Report No Deadline')], string='Project Progress Template',
        required=True, default='project_progress_no_deadline')
    link = fields.Char()
    sign_request_item_id = fields.Many2one('sign.request.item','SIGN REQUEST')
    sign_request_id = fields.Many2one('sign.request', readonly=True)
    weekly_hour_consumption_ids = fields.One2many("weekly.hour.consumption", "project_progress_id", readonly=False)

    @api.depends('project_id')
    def _compute_partner_ids(self):
        for rec in self:
            if rec.project_id.partner_id.parent_id:
                parent_partner = rec.project_id.partner_id.parent_id
                all_related_partners = parent_partner.child_ids | parent_partner
            else:
                all_related_partners = rec.project_id.partner_id.child_ids | rec.project_id.partner_id
            all_related_partners = all_related_partners.filtered(lambda e: e.email)
            if all_related_partners:
                rec.signatory_portal_report_partner_ids = all_related_partners
            else:
                rec.signatory_portal_report_partner_ids = False
            rec.cc_progress_report_internal_partner_partner_ids = self.env['res.users'].search(
                [('group_ids', 'in', [self.env.ref('base.group_user').id])]).mapped('partner_id') + all_related_partners

    def action_project_progress_send(self):
        self.ensure_one()
        mail_template = self.env.ref('cap_project_progress_report.project_progress_report_custom_mail_template')
        if self.project_progress_template == 'project_progress_with_deadline':
            report_template_id = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                "cap_project_progress_report.report_project_progress",
                res_ids=self.ids)
        elif self.project_progress_template == 'project_progress_no_deadline':
            report_template_id = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                "cap_project_progress_report.project_progress_report_no_deadline_id",
                res_ids=self.ids)
        else:
            report_template_id = False

        if report_template_id:
            data_record = base64.b64encode(report_template_id[0])
            today_date = date.today()
            ir_values = {
                'name': self.project_id.name + " - " + today_date.strftime("%Y-%m-%d") + ".pdf",
                'type': 'binary',
                'datas': data_record,
                'store_fname': data_record,
                'mimetype': 'application/x-pdf',
            }
            data_id = self.env['ir.attachment'].sudo().create(ir_values)

            sign_template_id = self.env['sign.template'].sudo().create({'attachment_id': data_id.id, 'active': False})

            self.env['sign.item'].sudo().create({
                'type_id': self.env.ref('sign.sign_item_type_signature').id,
                'required': True,
                'responsible_id': self.env.ref('sign.sign_item_role_default').id,
                'page': 1,
                'posX': 0.750,
                'posY': 0.08,
                'template_id': sign_template_id.id,
                'width': 0.200,
                'height': 0.050,
            })

            sign_request = self.env['sign.request'].with_user(SUPERUSER_ID).with_context({
                'no_sign_mail': True
            }).create({
                'template_id': sign_template_id.id,
                'reference': sign_template_id.display_name,
                'request_item_ids': [Command.create({
                    'partner_id': self.sudo().signatory_progress_report_partner_id.id,
                    'role_id': self.env.ref('sign.sign_item_role_default').id,
                })],
                'subject': sign_template_id.display_name,
                'message': "Sign to validate the Project Progress Report : {}".format(self.name),
                'attachment_ids': [Command.set(data_id.ids)],
            })

            self.sudo().sign_request_ids = [(4, sign_request.id)]
            self.sudo().sign_request_id = sign_request
            sign_request_item = sign_request.request_item_ids[0]
            self.sudo().sign_request_item_id = sign_request_item
            sign_request.with_user(SUPERUSER_ID).go_to_signable_document()
            timestamp = sign_request_item._generate_expiry_link_timestamp()
            expiry_hash = sign_request_item._generate_expiry_signature(sign_request_item.id, timestamp)

            self.link = url_join(sign_request_item.get_base_url(),
                                 "sign/document/mail/%(request_id)s/%(access_token)s?timestamp=%(timestamp)s&exp=%(exp)s" % {
                                     'request_id': sign_request.id,
                                     'access_token': sign_request_item.sudo().access_token,
                                     'timestamp': timestamp,
                                     'exp': expiry_hash
                                     })

            partner_lang = get_lang(self.env, lang_code=self.project_id.partner_id.lang).code

            ctx = {
                'default_model': 'project.progress',
                'active_model': 'project.progress',
                'active_id' : self.id,
                'default_res_ids': self.ids,
                'default_res_id': self.id,
                'default_use_template': bool(mail_template),
                'default_template_id': mail_template.id,
                'default_composition_mode': 'mass_mail',
                'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
                'force_email': True,
                'email_from': self.env.user.login,
                'email_cc': [partner.email for partner in self.cc_progress_report_partner_ids],
                'email_to': self.signatory_progress_report_partner_id.email,
                'reply_to': self.sign_request_item_id.create_uid.email,
                'is_notification': False,
                'lang': partner_lang}

            mail_send_wizard = self.env['mail.compose.message'].with_context(ctx).sudo().create({
                'attachment_ids': [(4, data_id.id)],
                'composition_mode': 'mass_mail',
                'template_id':mail_template.id,
            })
            mail_send_wizard.action_send_mail()
            # Mail is always in cancel state because of mail compose functionality so we manage it manually
            mail_record = self.env['mail.mail'].sudo().search([('model', '=', 'project.progress'), ('res_id', '=', self.id)],
                                                       order = 'create_date desc', limit=1)
            if mail_record and mail_record.state == 'cancel':
                mail_record.sudo().write({'state': 'outgoing'})

            self.write({'status': 'sent'})
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': """Email send Successfully! \n\n
                                           Check your Mailbox to Sign the document""",
                    'type': 'rainbow_man',
                }
            }

    @api.depends('project_id')
    def _get_last_report(self):
        for rec in self._origin:
            all_recs = rec.search([('project_id', '=', rec.project_id.id)])
            if all_recs:
                all_recs.write({'last_report': False})
                all_recs[-1].write({'last_report': True})

    @api.constrains('project_id', 'phase_id')
    def compute_project_domain_history(self):
        """
        This method is used to create project domain history based on phase and project and project domain
        """
        if not self.phase_id:
            self.project_domain_history_ids.unlink()
        for rec in self._origin:
            if not rec.project_id or not rec.phase_id:
                continue
            if rec.project_id.id != rec.phase_id.project_id.id:
                rec.phase_id = False
            project_domain_ids = rec.env['project.domain'].search(
                [('project_id', '=', rec.project_id.id), ('phase_id', '=', rec.phase_id.id)])
            old_project_domain_ids = rec.project_domain_history_ids
            vals_list = []
            for project_domain_id in project_domain_ids.sorted(key=lambda r: r.sequence):
                vals_list.append({'name': project_domain_id.name,
                                  'default_domain_id': project_domain_id.default_domain_id.id,
                                  'project_id': project_domain_id.project_id.id,
                                  'status': project_domain_id.status,
                                  'phase_id': project_domain_id.phase_id.id,
                                  'project_manager_time': project_domain_id.project_manager_time,
                                  'business_analyst_time': project_domain_id.business_analyst_time,
                                  'configurator_time': project_domain_id.configurator_time,
                                  'developer_time': project_domain_id.developer_time,
                                  'architect_time': project_domain_id.architect_time,
                                  'core_time': project_domain_id.core_time,
                                  'implementation_time': project_domain_id.implementation_time,
                                  'local_time': project_domain_id.local_time,
                                  'offshore_time': project_domain_id.offshore_time,
                                  'estimated_time': project_domain_id.estimated_time,
                                  'task_estimated_time': project_domain_id.task_estimated_time,
                                  'task_passed_time': project_domain_id.task_passed_time, 'date': date.today(),
                                  'project_domain_id': project_domain_id.id,
                                  'project_progress_id': rec.id
                                  })
            if vals_list:
                self.env['project.domain.history'].create(vals_list)
            old_project_domain_ids.unlink()

    def calculate_the_progress_remaining_hours(self):
        for project_domain_id in self.project_id.project_domain_ids.sorted(key=lambda r: r.sequence):
            if project_domain_id.id not in self.project_domain_history_ids.mapped(
                    'project_domain_id.id') and project_domain_id.phase_id and project_domain_id.phase_id.id == self.phase_id.id:
                self.env['project.domain.history'].create({
                    'name': project_domain_id.name,
                    'default_domain_id': project_domain_id.default_domain_id.id,
                    'project_id': project_domain_id.project_id.id,
                    'status': project_domain_id.status,
                    'phase_id': project_domain_id.phase_id.id,
                    'project_manager_time': project_domain_id.project_manager_time,
                    'business_analyst_time': project_domain_id.business_analyst_time,
                    'configurator_time': project_domain_id.configurator_time,
                    'developer_time': project_domain_id.developer_time,
                    'architect_time': project_domain_id.architect_time,
                    'core_time': project_domain_id.core_time,
                    'implementation_time': project_domain_id.implementation_time,
                    'local_time': project_domain_id.local_time,
                    'offshore_time': project_domain_id.offshore_time,
                    'estimated_time': project_domain_id.estimated_time,
                    'task_estimated_time': project_domain_id.task_estimated_time,
                    'task_passed_time': project_domain_id.task_passed_time, 'date': date.today(),
                    'project_domain_id': project_domain_id.id,
                    'project_progress_id': self.id
                })
        for pdh in self.project_domain_history_ids:
            if pdh.project_domain_id:
                pdh.status = pdh.project_domain_id.status
                pdh.estimated_time = pdh.project_domain_id.estimated_time
                pdh.task_estimated_time = pdh.project_domain_id.task_estimated_time
                pdh.task_passed_time = pdh.project_domain_id.task_passed_time
            else:
                self.project_domain_history_ids = [(3, pdh.id)]
        all_task_ids = self.env['project.task'].search(
            [('project_id', '!=', False), ('project_id', '=', self.project_id.id)])
        non_validated_tasks = all_task_ids.filtered(lambda r: not r.stage_id.is_validate)
        phase_all_tasks = all_task_ids.filtered(lambda rec: rec.default_phase_id == self.phase_id and not rec.parent_id)
        phase_all_hours = sum(phase_all_tasks.mapped('allocated_hours'))
        global_tasks = phase_all_tasks.filtered(lambda r: r.stage_id.stage or r.stage_id.is_validate)
        global_hours = sum(global_tasks.mapped('allocated_hours'))
        validated_tasks = phase_all_tasks.filtered(lambda r: r.stage_id.is_validate)
        validated_hours = sum(validated_tasks.mapped('allocated_hours'))
        out_of_scope_tasks = phase_all_tasks.filtered(lambda r: not r.parent_id and not r.project_requirement_id)
        out_of_scope_hours = sum(out_of_scope_tasks.mapped('allocated_hours'))

        # Calculation of Global Progress
        self.global_progress = global_hours / phase_all_hours if phase_all_hours > 0 else 1
        # Calculation of Validation Progress
        self.validation_progress = validated_hours / phase_all_hours if phase_all_hours > 0 else 1

        self.out_of_scope_included_in_current_phase = out_of_scope_hours

        # Calculation of Remaining Hours to Go Live
        self.remaining_hours = sum(non_validated_tasks.mapped('allocated_hours')) - sum(
            non_validated_tasks.mapped('effective_hours'))

        #Calculation of left hours
        self.left_hours = sum(
            self.project_id.sale_order_line_ids.filtered(lambda rec: rec.order_id.state in ('sale', 'done')).mapped(
                'x_studio_remaining_quantity'))

        weekly_consumption = self.env['weekly.hour.consumption'].search([
            ('project_progress_id', '=', self.id)
        ], limit=1)

        if not weekly_consumption:
            self.create_weekly_hour_consumption()
            weekly_consumption = self.env['weekly.hour.consumption'].search([
                ('project_progress_id', '=', self.id)
            ], limit=1)

        if weekly_consumption:
            consumed_hours = self.get_consumed_hours_by_week()

            weekly_consumption.write({
                'current_week': float_round((consumed_hours.get('current_week') or (None, 0))[1],precision_rounding=0.01),
                'week_tminusone': float_round((consumed_hours.get('week_1') or (None, 0))[1],precision_rounding=0.01),
                'week_tminustwo': float_round((consumed_hours.get('week_2') or (None, 0))[1],precision_rounding=0.01),
                'week_tminusthree': float_round((consumed_hours.get('week_3') or (None, 0))[1],precision_rounding=0.01),
            })

    @api.depends('project_id')
    def _get_left_progress(self):
        for rec in self:
            if rec.project_id:
                # Calculation of Hours Left In Current Bucket
                rec.left_hours = sum(rec.project_id.sale_order_line_ids.filtered(lambda rec:rec.order_id.state in ('sale', 'done')).mapped('x_studio_remaining_quantity'))
            else:
                rec.left_hours = 0.0

    @api.onchange('project_id', 'phase_id')
    def onchange_project(self):
        if self.project_id:
            self.project_progress_template = self.project_status_id.project_progress_template if self.project_status_id.project_progress_template else 'project_progress_no_deadline'
            self.signatory_progress_report_partner_id = self.project_id.signatory_progress_report_partner_id.id if self.project_id.signatory_progress_report_partner_id else False
            self.cc_progress_report_partner_ids = [(6, 0,
                                                 self.project_id.cc_progress_report_partner_ids.ids)] if self.project_id.cc_progress_report_partner_ids else False
            all_task_ids = self.env['project.task'].search(
                [('project_id', '=', self.project_id.id)])
            # ('project_id', '!=', False),
            all_task_ids_with_phase = all_task_ids.filtered(lambda r: r.default_phase_id == self.phase_id or not r.default_phase_id)
            non_validated_tasks = all_task_ids.filtered(lambda r: not r.stage_id.is_validate)
            phase_all_tasks = all_task_ids.filtered(lambda rec: rec.default_phase_id == self.phase_id and not rec.parent_id)
            phase_all_hours = sum(phase_all_tasks.mapped('allocated_hours'))
            global_tasks = phase_all_tasks.filtered(lambda r: r.stage_id.stage or r.stage_id.is_validate)
            global_hours = sum(global_tasks.mapped('allocated_hours'))
            validated_tasks = phase_all_tasks.filtered(lambda r: r.stage_id.is_validate)
            validated_hours = sum(validated_tasks.mapped('allocated_hours'))
            out_of_scope_tasks = phase_all_tasks.filtered(lambda r: not r.parent_id and not r.project_requirement_id)
            out_of_scope_hours = sum(out_of_scope_tasks.mapped('allocated_hours'))

            # Calculation of Global Progress
            self.global_progress = global_hours / phase_all_hours if phase_all_hours > 0 else 1
            # Calculation of Validation Progress
            self.validation_progress = validated_hours / phase_all_hours if phase_all_hours > 0 else 1

            self.out_of_scope_included_in_current_phase = out_of_scope_hours

            # Calculation of Remaining Hours to Go Live
            self.remaining_hours = sum(non_validated_tasks.mapped('allocated_hours')) - sum(
                non_validated_tasks.mapped('effective_hours'))

            # Set a Past Done Tasks Data
            old_tasks = []
            self.past_done_task_history_ids = [(6, 0, [])]
            old_meeting = self.search([('project_id', '=', self.project_id.id), ('id', '!=', self._origin.id)],
                                      limit=1, order='id desc')
            used_task = []
            for task in old_meeting.future_task_ids.filtered(lambda l: l.default_phase_id.id == self.phase_id.id):
                if task.id not in used_task:
                    old_tasks.append((0, 0, {
                        'project_id': task.project_id.id,
                        'task_id': task.id,
                        'is_planned': True,
                        'state': task.stage_id.name,
                    }))
                    used_task.append(task.id)
            for rec in all_task_ids_with_phase.mapped('timesheet_ids'):
                if rec.task_id.id not in used_task:
                    if old_meeting and old_meeting.create_date.date() <= rec.date <= fields.Date.today():
                        old_tasks.append((0, 0, {
                            'project_id': rec.project_id.id,
                            'task_id': rec.task_id.id,
                            'is_planned': False,
                            'state': rec.task_id.stage_id.name,
                        }))
                        used_task.append(rec.task_id.id)
                    elif rec.date <= fields.Date.today() and not old_meeting:
                        old_tasks.append((0, 0, {
                            'project_id': rec.project_id.id,
                            'task_id': rec.task_id.id,
                            'is_planned': False,
                            'state': rec.task_id.stage_id.name,
                        }))
                        used_task.append(rec.task_id.id)

            self.past_done_task_history_ids = old_tasks

            # Set a Hold Tasks Data
            self.hold_task_ids = [(6, 0, all_task_ids_with_phase.filtered(lambda r: r.stage_id.hold).ids)]

            # Set a Future Tasks Data
            tasks = []
            for task in self.project_id.task_ids.filtered(lambda l: l.default_phase_id.id == self.phase_id.id):
                if (task.planned_date_begin and task.planned_date_begin.date() <= (fields.Date.today() + timedelta(days=7))
                        and (task.planned_date_start == False or task.planned_date_start.date() >= fields.Date.today())):
                    tasks.append(task.id)
            self.future_task_ids = [(6, 0, tasks)]

            # Set a Sale order Line Data
            so_lines = self.project_id.sale_order_line_ids.filtered(lambda r: r.order_id.state in ('sale', 'done') and r.x_studio_remaining_quantity > 0.5)
            # so_lines += self.project_id.sale_order_line_ids.filtered(lambda r: r.product_id.service_policy == 'delivered_timesheet')
            # so_lines = sorted(so_lines, key=lambda p: p.id, reverse=True)
            if so_lines:
                self.sale_order_line_ids = [(6, 0, so_lines.ids)]
            last_project_progress = self.search([('project_id', '=', self.project_id.id)], order='id DESC', limit=1)
            self.demo_meeting_task = last_project_progress.demo_meeting_task
            self.message = last_project_progress.message

    def change_planned_date(self):
        tasks = self.future_task_ids.filtered(lambda t: t.select)
        for task in tasks:
            if not task.planned_date_begin:
                raise ValidationError('Start date is not set on!!!')
            task.write({'select': False, 'planned_date_begin': task.planned_date_begin + timedelta(days=self.days)})

        self.write({'future_task_ids': [(3, task.id) for task in tasks]})

    @api.model_create_multi
    def create(self, vals):
        """
        To avoid error 'One parameter is missing to use this method. You should give a start and end dates.' From base,
        When we create project progress report.
        """
        res = super(ProjectProgress, self.with_context(from_project_progress=True)).create(vals)
        for rec in res:
            rec.create_weekly_hour_consumption()
        return res

    def _get_mail_link(self, email, subject):
        return "mailto:%s?subject=%s" % (url_quote(email), url_quote(subject))

    def create_weekly_hour_consumption(self):
        """
        Create a weekly.hour.consumption record when a project progress is created.
        """
        consumed_hours = self.get_consumed_hours_by_week()

        # Create weekly hour consumption record
        self.env['weekly.hour.consumption'].create({
            'current_week': float_round((consumed_hours.get('current_week') or (None, 0))[1],precision_rounding=0.01),
            'week_tminusone': float_round((consumed_hours.get('week_1') or (None, 0))[1],precision_rounding=0.01),
            'week_tminustwo': float_round((consumed_hours.get('week_2') or (None, 0))[1],precision_rounding=0.01),
            'week_tminusthree': float_round((consumed_hours.get('week_3') or (None, 0))[1],precision_rounding=0.01),
            'project_progress_id': self.id,
        })

    def get_consumed_hours_by_week(self):
        existing_weekly_consumption = self.env['weekly.hour.consumption'].search([
            ('project_progress_id', '=', self.id)
        ], limit=1)
        if len(existing_weekly_consumption) == 1:
            today = existing_weekly_consumption.write_date.date()
        else:
            today = fields.Date.today()
        week_start = today - timedelta(days=today.weekday())
        week_starts = {
            'week_3': week_start - timedelta(weeks=3),
            'week_2': week_start - timedelta(weeks=2),
            'week_1': week_start - timedelta(weeks=1),
            'current_week': week_start
        }
        consumed_hours = {
            'week_3': 0,
            'week_2': 0,
            'week_1': 0,
            'current_week': 0
        }
        week_numbers = {}
        total_timesheets_on_project = self.env['account.analytic.line'].sudo().search([('project_id', '=', self.project_id.id)])

        for week_key, week_start_date in week_starts.items():
            week_end_date = week_start_date + timedelta(days=6)
            consumed_hours[week_key] = sum(total_timesheets_on_project.filtered(lambda line: week_start_date <= line.date <= week_end_date).mapped('unit_amount'))
            week_numbers[week_key] = ('Week-' + str(week_start_date.isocalendar()[1]), consumed_hours[week_key])

        return week_numbers
