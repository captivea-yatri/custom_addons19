# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import random
import requests
import json


class SkillValidationRequest(models.Model):
    _name = 'hr.skill.validation.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Skill validator Request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id.id)
    status = fields.Selection(
        [('requested', 'Requested'), ('scheduled', 'Scheduled'), ('succeed', 'Succeed'), ('failed', 'Failed')],
        string='Status', default='requested', copy=False)
    skill_id = fields.Many2one(
        'hr.skill',
        string='Skill',
        tracking=True,
        ondelete='set null',
        context={'active_test': False},
        domain=[],
    )

    url = fields.Char(string='Url')
    validator_id = fields.Many2one('res.users', string='Validator',
                                   context={'active_test': False},
                                   domain=lambda self: [('share', '=', False)],ondelete='set null')
    request_to_be_private = fields.Boolean(string='Request To Be Private')
    is_login_user = fields.Boolean(string='Is Login USER', compute='_compute_is_login_user')
    type_of_valivation = fields.Selection(string='Type Of Valivation', related='skill_id.type_of_valivation', store=True)
    is_login_user_employee = fields.Boolean(string='Is Login User Employee', compute='_compute_is_login_user_employee')
    survey_user_input_id = fields.Many2one('survey.user_input', string='Survey User Input')

    def copy(self, default=None):
        """
        Change the status when duplicate skill request.
        """
        #TODO: Check and if not needed remove this method
        if default is None:
            default = {}
            if self.status == 'requested':
                default['status'] = 'failed'
            else:
                default['status'] = 'requested'
        return super(SkillValidationRequest, self).copy(default)

    def create_activity(self, check_to_survey=False):
        """
                Create a skill validation activity or send a survey invitation.

                - For non-certification skills: creates a 'To Do' activity for the validator.
                - For certification skills (when `check_to_survey` is True): sends a survey invite
                  to the employee and updates the request status to 'scheduled'.
                """
        if self.type_of_valivation != 'certification':
            self.env['mail.activity'].sudo().with_context(mail_activity_quick_update=True).create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_model_id': self.env.ref('cap_hr_skill.model_hr_skill_validation_request').id,
                'res_id': self.id,
                'automated': True,
                'user_id': self.validator_id.id,
                'summary': 'Skill Validation Request',
            })
        if check_to_survey and self.type_of_valivation == 'certification' and self.skill_id.survey_id:
            survey_wizard_value = {
                'subject': _('Participate For %s Skill Validation.' % (self.skill_id.name)),
                'survey_id': self.skill_id.survey_id.id,
                'partner_ids': [(4, self.employee_id.user_id.sudo().partner_id.id)],
                'existing_mode': 'new',
                'template_id': self.env.ref('survey.mail_template_user_input_invite').id
            }
            survey_send_invite = self.env['survey.invite'].with_user(SUPERUSER_ID).create(survey_wizard_value)
            survey_send_invite.with_user(SUPERUSER_ID).with_context(skill_request_id=self.id).action_invite()
            if survey_send_invite:
                self.status = 'scheduled'

    @api.model_create_multi
    def create(self, vals):
        """
                Override create to automatically trigger activity creation.
        """
        res = super(SkillValidationRequest, self).create(vals)
        res.create_activity(True)
        return res

    def write(self, vals):
        """
                Override write to manage survey and activity updates on skill changes.

                - Removes existing survey input if the skill is changed.
                - Recreates activity when `skill_id` or `validator_id` is updated.
        """
        if 'skill_id' in vals:
            survey_user_input = self.survey_user_input_id
            if survey_user_input:
                survey_user_input.sudo().unlink()
            vals['survey_user_input_id'] = False
        res = super(SkillValidationRequest, self).write(vals)
        for rec in self:
            if any(k in vals for k in ['skill_id', 'validator_id']):
                rec.create_activity(True and 'skill_id' in vals or False)
        return res

    @api.constrains('skill_id', 'employee_id', 'value_of_limitation_skill_request')
    def check_employee_skill_and_validation_request(self):
        """
               Validate employee skill requests to prevent duplicates and overuse.

               - Disallows requesting validation for the same skill within 15 days.
               - Restricts repeated validation requests of the same type within a week,
                 based on the company’s defined limitation.
               - Blocks validation if the employee already possesses the skill.
               """
        previous_date = datetime.now() - timedelta(days=15)
        for rec in self:
            prev_requests_for_15_days = self.search([('skill_id', '=', rec.skill_id.id),
                                                     ('employee_id', '=', rec.employee_id.id),
                                                     ('create_date', '>=', previous_date),
                                                     ('id', '!=', rec.id)])
            if prev_requests_for_15_days:
                raise ValidationError('You cannot request for the same skill validation within 15 days!')

            if rec.type_of_valivation != False:
                previous_week = datetime.now() - timedelta(days=7)
                prev_requests_for_an_week_ids = self.search([('create_date', '>=', previous_week),
                                                             ('type_of_valivation', '=', rec.type_of_valivation),
                                                             ('employee_id', '=', rec.employee_id.id)])
                if len(prev_requests_for_an_week_ids) > self.employee_id.company_id.limitation_of_skill_request:
                    raise ValidationError(
                        f'You cannot request for the same Type Of Validation more than '
                        f'{self.employee_id.company_id.limitation_of_skill_request} times in a week!')
            existing_employee_skill_ids = self.env['hr.employee.skill'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('skill_id', '=', rec.skill_id.id),
            ])
            if existing_employee_skill_ids:
                raise ValidationError('Skill already exists. You cannot request again for validation!')

    @api.onchange('skill_id')
    def onchange_skill(self):
        """
                Auto-assign a validator when a skill is selected.

                - Finds a validator linked to the skill’s domain and employee’s company.
                - If multiple validators exist, randomly selects one.
                - If no validator is found, defaults to user ID 42.
                """
        if self.skill_id:
            company_id = self.employee_id.company_id
            hr_skill_validator_ids = self.env['hr.skill.validator'].search(
                [('domain_skill_id', '=', self.skill_id.domain_skill_id.id), ('companies_ids', '=', company_id.id)])
            if not hr_skill_validator_ids:
                hr_skill_validator_ids = self.env['hr.skill.validator'].search(
                    [('domain_skill_id', '=', self.skill_id.domain_skill_id.id), ('companies_ids', '=', False)])
            if hr_skill_validator_ids:
                if len(hr_skill_validator_ids) == 1:
                    self.validator_id = hr_skill_validator_ids.validator_id.id
                elif len(hr_skill_validator_ids) > 1:
                    random_validator = random.choice(hr_skill_validator_ids)
                    self.validator_id = random_validator.validator_id.id
            else:
                self.validator_id = 42

    def action_scheduled(self):
        """
               Set the skill validation request status to 'Scheduled'.
         """
        for rec in self:
            rec.status = 'scheduled'

    def action_success(self):
        """
                Mark the skill validation request as successful and assign the skill to the employee.

                - Creates a new employee skill record if not already present.
                - Determines the appropriate skill level (default or highest).
                - Sends a congratulatory message via webhook if configured.
                - Updates the request status to 'succeed' and closes related activities.
                """
        for rec in self:
            skill_id = rec.skill_id
            existing_skills = rec.employee_id.employee_skill_ids.filtered(lambda s: s.skill_id == rec.skill_id)
            if not existing_skills:
                skill_level_ids = self.env['hr.skill.level'].search([
                    ('skill_type_id', '=', skill_id.skill_type_id.id)])
                default_level_ids = skill_level_ids.filtered(lambda x: x.default_level == True)
                skill_level_id = False
                if default_level_ids:
                    skill_level_id = max(default_level_ids.ids)
                elif skill_level_ids:
                    skill_level_id = max(skill_level_ids.ids)

                if skill_level_id:
                    values = {
                        'employee_id': rec.employee_id.id,
                        'skill_id': skill_id.id,
                        'skill_type_id': skill_id.skill_type_id.id,
                        'skill_level_id': skill_level_id,
                    }
                    res = self.env['hr.employee.skill'].sudo().create(values)
                    url = self.env['ir.config_parameter'].sudo().get_param('cap_hr_skill.url')
                    if res and url:
                        headers = {'Content-Type': "application/json"}
                        data = {
                            "activity": "OdooBot - " + res.employee_id.user_id.name,
                            "title": 'Congratulations To ' + res['employee_id'][
                                'name'] + '\n' + ' for having Successfully passed the ' + res['skill_id'][
                                         'name'] + '\n' + " - Good job",
                            "text": " ",
                        }

                        requests.post(url, data=json.dumps(data), headers=headers)
            rec.status = 'succeed'
            rec.to_do_done_activity()

    def action_failed(self):
        """
                  Set the skill validation request status to 'Failed'.
        """
        for rec in self:
            rec.status = 'failed'
            rec.to_do_done_activity()

    def to_do_done_activity(self):
        """
                Mark the validator's related 'Skill Validation Request' activity as done.

                - Finds all automated activities linked to the current skill validation request.
                - Completes them to indicate the process has been finalized.
        """
        activity_ids = self.env['mail.activity'].sudo().search([
            ('res_id', '=', self.id),
            ('automated', '=', True),
            ('user_id', '=', self.validator_id.id),
            ('summary', '=', 'Skill Validation Request')])
        activity_ids.action_done()

    @api.depends('validator_id')
    def _compute_is_login_user(self):
        """
                Compute whether the logged-in user is the assigned validator.

                - Sets 'is_login_user' to True if the current user matches the record's validator.
        """
        for record in self:
            record.is_login_user = record.validator_id == self.env.user

    @api.depends('employee_id')
    def _compute_is_login_user_employee(self):
        """
            Compute whether the logged-in user is the employee who made the request.

            - Sets 'is_login_user_employee' to True if:
                - The request status is 'requested', and
                - The logged-in user is the employee's linked user.
        """
        for record in self:
            if record.status == 'requested' and record.employee_id.user_id == self.env.user:
                record.is_login_user_employee = True
            else:
                record.is_login_user_employee = False
