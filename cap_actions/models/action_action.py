from odoo import fields, models, api
from datetime import date, timedelta

class Action(models.Model):
    _name = 'action.action'
    _description = 'Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', compute='_compute_name')
    
    template_id = fields.Many2one('action.template', string='Template')
    validation_ids = fields.One2many('action.validation', 'action_id', string="Validations")

    status = fields.Selection([
        ('todo', 'To Do'),
        ('invalidation', 'In Validation'),
        ('done', 'Done')
    ], string='Status', tracking=True)
    
    date = fields.Date('Date')
    deadline = fields.Date('Deadline')
    
    user_id = fields.Many2one('res.users', string='User', tracking=True)
    company_id = fields.Many2one('res.company', string='Company')
    
    current_sequence = fields.Integer(string='Current Sequence', help="Used to order. Lower is better.", default=1000)
    
    scoreimpact = fields.Integer(string='Score Impact')
    
    resolution_status = fields.Selection([
        ('ontime', 'On Time'),
        ('inlate', 'In Late'),
    ], string='Resolution Status', tracking=True)
    
    is_current_user_validator = fields.Boolean(compute='_compute_is_current_user_validator')
    
    description = fields.Html(string='Description')
    
    def _compute_is_current_user_validator(self):
        """
            Compute whether the current logged-in user is a validator for this action.
            (Show validation tab or buttons when the current user is one of the validators).
        """
        for rec in self:
            rec.is_current_user_validator = False
            for validation in rec.validation_ids:
                if validation.user_id.id == self._uid:
                    rec.is_current_user_validator = True
           
    
    def _compute_name(self):
        """
            Compute a human-friendly name for the action record.
        """
        for a in self:
            a.name = (a.template_id.name or '') + ' for ' + (a.company_id.name or '') + " at " + (str(a.date) if a.date else '')

    
    def set_status_done(self):
        """
            Transition the action from 'todo' to 'invalidation' (mark as done by responsible).
            Behaviour:
                - Sets `status` to 'invalidation'.
                - Computes `resolution_status` as 'ontime' or 'inlate' by comparing the
                  `deadline` to today's date.
                - Calls `calculate_next_sequence()` to find and activate the first validator.
        """
        today = date.today()
        
        self.status = 'invalidation'
        if self.deadline < today:
            self.resolution_status = 'inlate'
        else:
            self.resolution_status = 'ontime'
        self.calculate_next_sequence()

    def set_status_reset(self):
        """
            Reset the action status back to 'todo'.
        """
        self.status = 'todo'
    
    def calculate_next_sequence(self):
        """
            Activate the next pending or failed validation in ascending sequence order.
                Algorithm summary:
                1. Iterate through all `validation_ids`.
                2. Consider validations whose status is 'tovalidate' or 'failed'.
                3. Choose the smallest sequence number among those (lowest sequence = earliest).
                4. If found:
                    - Set `current_sequence` on the action to that sequence.
                    - Schedule a mail activity for the validator (using activity key
                      'approvals.mail_activity_data_approval' and the validator user).
                    - Set that validation's status to 'tovalidate' (using sudo to ensure
                      the scheduler can update it).
                5. If none found:
                    - Mark the action `status = 'done'`.
        """
        sequence_found = False
        sequence = 1000
        current_validation = False
        
        for validation in self.validation_ids:
            if validation.status == 'tovalidate' or validation.status == 'failed':
                if sequence >= validation.sequence:
                    sequence_found = True
                    sequence = validation.sequence
                    current_validation = validation
        if sequence_found:
            self.current_sequence = sequence
            self.activity_schedule(
                'approvals.mail_activity_data_approval',
                user_id=current_validation.user_id.id)
            current_validation.sudo().status = 'tovalidate'
        else:
            self.status = 'done'
    
    def calculate_previous_sequence(self):
        """
               Move the validation flow backwards to the previous completed validation.

               Purpose:
               - Called when a validation fails later and the workflow needs to go back
                 to a prior validator (for re-validation or escalation).

               Algorithm summary:
               1. Start from current action `current_sequence`.
               2. Iterate through validation lines and find validations with status 'done'.
               3. Find the most recent validation whose sequence is less than the current one:
                  - The logic attempts to find the highest sequence among those which are
                    less than the current_sequence, using an 'already_downgrade' flag to
                    pick the immediate prior step.
               4. If such a previous validation is found:
                  - Set `current_sequence` to that sequence.
                  - Schedule a mail.activity for that validator.
                  - Set that validation's status to 'tovalidate' (sudo).
               5. If none found:
                  - Set action status back to 'todo'.
               """
        sequence_found = False
        already_downgrade = False
        sequence = self.current_sequence
        current_validation = False
        #todo
        for validation in self.validation_ids:
            if validation.status == 'done':
                if already_downgrade == False:
                    if validation.sequence < sequence:
                        already_downgrade = True
                        sequence_found = True
                        sequence = validation.sequence
                        current_validation = validation
                else:
                    if validation.sequence > sequence:
                        sequence = validation.sequence
                        current_validation = validation
        if sequence_found:
            self.current_sequence = sequence
            self.activity_schedule(
                'approvals.mail_activity_data_approval',
                user_id=current_validation.user_id.id)
            current_validation.sudo().status = 'tovalidate'
        else:
            self.status = 'todo'

