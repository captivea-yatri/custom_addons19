# -*- coding: utf-8 -*-
from odoo import models, fields, _, api


class ProjectFeedback(models.Model):
    _name = 'project.feedback'
    _inherit = ['portal.mixin','mail.thread', 'mail.activity.mixin','utm.mixin']
    _description = 'Project Feedback'

    name = fields.Text(required=True, tracking=True)
    project_id = fields.Many2one(comodel_name="project.project", tracking=True)
    assignee_id = fields.Many2one(comodel_name="hr.employee", tracking=True)
    description = fields.Html(string='Description')
    estimated_effort = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('hard', 'Hard')],
                                        string="Estimated effort")
    maturity = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Medium'), ('3', 'High')], default="1",
                                tracking=True)
    phase_id = fields.Many2one(comodel_name='project.phase', string="Phase", domain="[('project_id', '=', project_id)]")
    domain_id = fields.Many2one('project.domain', string='Domain', domain="[('project_id', '=', project_id)]")
    default_domain_ids = fields.Many2many('default.domain', 'project_default_domain_rel', 'project_id', 'domain_id',
                                          string='Default Domains', related='project_id.default_domain_ids')
    default_domain_id = fields.Many2one('default.domain', string='Default Domain',tracking=True)
    estimated_hours = fields.Float(string="Estimated Hours", tracking=True)
    impact_on_timeline = fields.Text()
    transformed_in_task = fields.Boolean('Transformed In Task')
    status = fields.Selection([('new', 'New'), ('pending_estimation', 'Pending Estimation'),
                               ('waiting_feedback_arbitration', 'Waiting Feedback Arbitration'),
                               ('postpone', 'PostPone'), ('validated_task_created', 'Closed : Validated task created'),
                               ('linked', 'Closed : duplicate'), ('cancelled', 'Closed : cancelled')], default='new', tracking=True)
    task_id = fields.Many2one(comodel_name="project.task", tracking=True, domain="[('project_id', '=', project_id)]")
    tag_ids = fields.Many2many('project.tags', 'project_tag_rel', 'feedback_id', 'tag_id', string="Tags")


    def _send_invite_for_feedback(self, partner_ids, send_mail):
        if partner_ids:
            invite_wizard = self.env['mail.wizard.invite'].sudo().create({
                'res_model': 'project.feedback',
                'res_id': self.id,
                'partner_ids': [(4, partner_id.id) for partner_id in partner_ids],
                'message': _('You have been invited to follow this Project Feedback: %s') % self.name,
                'notify': send_mail,
            })
            invite_wizard.sudo().add_followers()

    @api.model_create_multi
    def create(self, vals_list):
        rec = super(ProjectFeedback, self.sudo()).create(vals_list)
        for feedback in rec:
            # pm_of_customer = feedback.project_id.signatory_progress_report_partner_id
            # if pm_of_customer:
            #     feedback._send_invite_for_feedback(partner_ids=pm_of_customer, send_mail=True)
            if self.env.context.get('is_created_from_website'):
                id_of_partner_of_pm = feedback.project_id.user_id.partner_id
                if id_of_partner_of_pm:
                    feedback._send_invite_for_feedback(partner_ids=id_of_partner_of_pm, send_mail=True)
            if feedback.task_id.user_ids:
                task_partners = feedback.task_id.user_ids.mapped('partner_id')
                if task_partners:
                    feedback._send_invite_for_feedback(partner_ids=task_partners,send_mail=True)
            if feedback.assignee_id:
                self._task_message_auto_subscribe_notify({feedback: feedback.assignee_id.user_id})
                partner_for_asignee = feedback.assignee_id.user_id.partner_id
                feedback._send_invite_for_feedback(partner_ids=partner_for_asignee,send_mail=False)
        return rec

    def write(self, vals):
        feedback = super(ProjectFeedback, self).write(vals)
        if vals.get('assignee_id'):
            new_assignee = self.env['hr.employee'].browse(vals['assignee_id'])
            if new_assignee:
                self._task_message_auto_subscribe_notify({self: new_assignee.user_id})
                partner_for_asignee = new_assignee.user_id.partner_id
                if partner_for_asignee:
                    self._send_invite_for_feedback(partner_ids=partner_for_asignee,send_mail=False)
        if vals.get('task_id'):
            new_task = self.env['project.task'].browse(vals['task_id'])
            users = new_task.sudo().user_ids
            if users:
                task_partners = new_task.sudo().user_ids.mapped('partner_id')
                if task_partners:
                    self._send_invite_for_feedback(partner_ids=task_partners, send_mail=True)
        return feedback

    def _compute_access_url(self):
        super()._compute_access_url()
        for feedback in self:
            feedback.access_url = f'/my/feedback/readonly/{feedback.id}'

    def _notify_get_recipients_groups(self, message, model_description, msg_vals=None):
        groups = super()._notify_get_recipients_groups(message, model_description, msg_vals=msg_vals)
        if not self:
            return groups
        self.ensure_one()
        follower_group = next(group for group in groups if group[0] == 'follower')
        follower_group[2]['active'] = True
        follower_group[2]['has_button_access'] = True
        return groups

    @api.onchange('default_domain_id', 'phase_id')
    def set_project_domain(self):
        for rec in self:
            if rec.project_id and rec.default_domain_id and rec.phase_id:
                project_domain_id = self.env['project.domain'].search([('phase_id', '=', rec.phase_id.id),
                                                                        ('project_id', '=', rec.project_id.id),
                                                                        ('default_domain_id', '=', rec.default_domain_id.id)], limit=1)
                if project_domain_id:
                    rec.domain_id = project_domain_id.id
                else:
                    project_domain_id = self.env['project.domain'].create({
                        'project_id': rec.project_id.id,
                        'phase_id': rec.phase_id.id,
                        'default_domain_id': rec.default_domain_id.id
                    })
                    rec.domain_id = project_domain_id.id

    def transform_feedback_into_task(self):
        task_vals = {
            'name': self.name,
            'description': self.description,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
            'allocated_hours': self.estimated_hours,
            'project_id': self.project_id.id,
            'project_domain_id': self.domain_id.id,
            'default_domain_id': self.domain_id.default_domain_id.id,
            'default_phase_id': self.phase_id.id,
            'partner_id': self.project_id.partner_id.id
        }
        if self.assignee_id:
            task_vals.update({'user_ids': [(4, self.assignee_id.user_id.id)]})
        task_id = self.env['project.task'].create(task_vals)
        self.write({'task_id': task_id.id, 'transformed_in_task': True})

    def action_read_feedback(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.feedback',
            'res_id': self.id,
            'view_id': self.env.ref('cap_project_feedback.new_project_feedback_form_view_id').id,
            'context': {'default_project_id': self.project_id.id}
        }

    @api.model
    def _task_message_auto_subscribe_notify(self, users_per_feedback):
        # Utility method to send assignation notification upon writing/creation.
        template_id = self.env['ir.model.data']._xmlid_to_res_id('project.project_message_user_assigned',
                                                                 raise_if_not_found=False)
        if not template_id:
            return
        task_model_description = self.env['ir.model']._get(self._name).display_name
        for feedback, users in users_per_feedback.items():
            if not users:
                continue
            values = {
                'object': feedback,
                'model_description': task_model_description,
                'access_link': feedback._notify_get_action_link('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = self.env['ir.qweb']._render('project.project_message_user_assigned', values,
                                                              minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)
                feedback.message_notify(
                    subject=_('You have been assigned to %s', feedback.display_name),
                    body=assignation_msg,
                    partner_ids=user.partner_id.ids,
                    record_name=feedback.display_name,
                    email_layout_xmlid='mail.mail_notification_layout',
                    model_description=task_model_description,
                    mail_auto_delete=False,
                )
