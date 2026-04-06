# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError


class GoLiveCR(models.Model):
    _name = "glive.change.request"
    _description = "Go Live Change Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _rec_name = 'project_id'

    project_id = fields.Many2one('project.project', string='Project', copy=False, tracking=True)
    company_id = fields.Many2one('res.company', related="project_id.company_id", store=True, string='Company')
    glcr_steps = fields.Selection(string='Go Live Change Request Steps',related='company_id.glcr_steps')
    # state = fields.Selection([('requested', 'Requested'), ('manager_approved','Approved by manager'),
    #                           ('direction_approved', 'Approved by direction and applied')], string='Status',
    #                          default='requested', tracking=True)
    # Previously we were following group and managing approval. which is changed to step approval configuration on company.
    # And there are many records exist which not breaks the flow so we have just change the string(value) of the state,
    # Not key of the state.
    state = fields.Selection([('requested', 'Requested'), ('manager_approved', 'Approved'),
                              ('direction_approved', 'Validated')], string='Status',
                             default='requested', tracking=True)
    current_go_live_date = fields.Date('Current Go Live Date', tracking=True, compute='_go_live_date', store=True)
    new_go_live_date = fields.Date('New Go Live Date', tracking=True)
    reason = fields.Selection([('first_setting', 'First setting for end of analysis / First setting for phase X go live date'),
                               ('in_late', 'We are late due to Captivea and the customer is aware of the new go live date'),
                               ('additional_features','We are late due to the customer, the customer agreed and the customer approved the new go live date')],
                              string='Reason', tracking=True)
    proof = fields.Text(string='Proof', help='Explain the proof you have and add any justification to this request. '
                                             'Proof that you inform the customer, Prove that you get an approval from '
                                             'the customer', tracking=True)
    next_approver_user_id = fields.Many2one('res.users', 'Next Approver User', compute="_compute_next_approver",
                                            store=True)

#Todo: check this functionality when cap_offer migrate
    # @api.depends('company_id', 'company_id.glcr_steps', 'company_id.glcr_s2_validater',
    #              'state')
    # def _compute_next_approver(self):
    #     for rec in self:
    #         if rec.company_id.glcr_steps and rec.state == 'requested' and rec.company_id.offer_ids:
    #             for offer in rec.company_id.offer_ids:
    #                 if rec.project_id.offer_id == offer.offer_id:
    #                     rec.next_approver_user_id = offer.user_id
    #         elif rec.company_id.glcr_steps and rec.state == 'manager_approved' and rec.company_id.glcr_s2_validater:
    #             rec.next_approver_user_id = rec.company_id.glcr_s2_validater
    #         else:
    #             rec.next_approver_user_id = False

    @api.depends('project_id')
    def _go_live_date(self):
        """
               Compute method for 'current_go_live_date'.

               Purpose:
                   Automatically sets the current go-live date of the project on the change request.
               """
        if self.project_id:
            self.current_go_live_date = self.project_id.x_studio_go_live_date
        else:
            self.current_go_live_date = ''

    # Todo: check this functionality when cap_offer migrate
    # def approve_manager_approval(self):
    #     for rec in self:
    #         glcr_s1_validater = False
    #         for offer in rec.company_id.offer_ids:
    #             if rec.project_id.offer_id == offer.offer_id:
    #                 glcr_s1_validater = offer.user_id
    #         if not rec.company_id.glcr_steps:
    #             raise ValidationError('Please configure go live change request steps on company.')
    #         if not glcr_s1_validater:
    #             raise ValidationError(f'Validator missing: The offer "{rec.project_id.offer_id.name}" does not have a configured validator for {rec.company_id.name}.')
    #         if not self.env.user.id == glcr_s1_validater.id:
    #             raise ValidationError(f'You do not have the required authorization to approve. Please contact {glcr_s1_validater.name} to proceed further.')
    #         if rec.company_id.glcr_steps == '1' and self.env.user.id == glcr_s1_validater.id:
    #             rec.state = 'direction_approved'
    #             rec.project_id.x_studio_go_live_date = rec.new_go_live_date
    #             self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model_id', '=', self.env.ref(
    #                 'ksc_project_go_live_maintainer.model_glive_change_request').id)])._action_done()
    #         elif rec.company_id.glcr_steps == '2' and self.env.user.id == glcr_s1_validater.id:
    #             rec.state = 'manager_approved'
    #             self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model_id', '=', self.env.ref(
    #                 'ksc_project_go_live_maintainer.model_glive_change_request').id)])._action_done()
    #             self.create_activity()

    def direction_applied_manager_approval(self):
        """
              Action method to perform the second-level approval (Direction level).

              Purpose:
                  Validates the go-live change request at the final step, applies the new go-live date,
                  and marks related activities as done.

              Logic:
                  1. Checks if go-live change request steps are configured for the company.
                  2. Ensures that the current user is authorized as the second-level validator.
                  3. If authorized and the configuration step count is '2':
                     - Update the request state to 'direction_approved'.
                     - Update the project's `x_studio_go_live_date` with the new date.
                     - Mark all related activities as done.
              """
        for rec in self:
            if not rec.company_id.glcr_steps:
                raise ValidationError('Please configure go live change request steps on company.')
            if not self.env.user.id == rec.company_id.glcr_s2_validater.id:
                raise ValidationError('You are not authorized to proceed for next step, Please contact admin.')
            elif rec.company_id.glcr_steps == '2' and self.env.user.id == rec.company_id.glcr_s2_validater.id:
                rec.state = 'direction_approved'
                rec.project_id.x_studio_go_live_date = rec.new_go_live_date
                self.env['mail.activity'].search([('res_id', '=', self.id), ('res_model_id', '=', self.env.ref(
                    'ksc_project_go_live_maintainer.model_glive_change_request').id)])._action_done()

    @api.model_create_multi
    def create(self, vals_list):
        """
              Override of the Odoo create method.

              Purpose:
                  Automatically triggers creation of approval activities after creating a new record.
              """
        res = super(GoLiveCR, self).create(vals_list)
        res.create_activity()
        return res

    def create_activity(self):
        """
            Helper method to create a new approval activity for the next approver.
            Logic:
                - Checks if `next_approver_user_id` is set.
                - Creates a mail activity of type 'To Do' for that user.
                - If not configured, raises a validation error.
            """
        if self.next_approver_user_id:
            self.env['mail.activity'].sudo().create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_model_id': self.env.ref('ksc_project_go_live_maintainer.model_glive_change_request').id,
                'res_id': self.id,
                'user_id': self.next_approver_user_id.id,
                'summary': 'To review',
            })
        else:
            raise ValidationError(f'Please Configure "Go Live Change Request Steps" and its validators on company {self.company_id.name} first !')

    def unlink(self):
        """
         Ensures that only newly created (requested) Go Live Change Requests can be deleted.
        """
        for rec in self:
            if rec.state != 'requested':
                raise ValidationError(_('Only new request can be deleted!'))
        super(GoLiveCR, self).unlink()