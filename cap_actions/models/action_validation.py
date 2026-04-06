from odoo import fields, models, api

class ActionValidation(models.Model):
    _name = 'action.validation'
    _description = 'Action Validation'
    
    action_id = fields.Many2one('action.action', string='Action')
    template_validation_id = fields.Many2one('action.template.validation', string='Template Validation')
    user_id = fields.Many2one('res.users', string='Validator')
    sequence = fields.Integer(string='Sequence', help="Used to order. Lower is better.")

    current_sequence = fields.Integer(related='action_id.current_sequence')
    status = fields.Selection([
        ('tovalidate', 'To Validate'),
        ('failed', 'Failed'),
        ('done', 'Done')
    ], string='Status')
    
    is_current_user = fields.Boolean(compute='_compute_is_current_user')
    
    is_same_sequence = fields.Boolean(compute='_compute_same_sequence')
    
    def _compute_same_sequence(self):
        """
            Compute whether this validation's sequence matches the action's current_sequence.
            For each validation record, sets `is_same_sequence` to True when:
                validation.sequence == action_id.current_sequence
        """

        for rec in self:
            if rec.sequence == rec.current_sequence:
                rec.sudo().is_same_sequence = True
            else:
                rec.sudo().is_same_sequence = False
    
    def _compute_is_current_user(self):
        """
                Compute whether the logged-in user is the validator for this line.
        """
        for rec in self:
            if rec.user_id.id == self._uid:
                rec.sudo().is_current_user = True
            else:
                rec.sudo().is_current_user = False
                
                
    
    def set_status_done(self):
        """
                Mark this validation as done (approved).

                Effects / steps:
                1. Set this validation's `status` to 'done' using sudo().
                2. Remove any mail.activity entries assigned to this validator that refer
                   to the parent action to avoid duplicate reminders.
                3. Trigger the parent action's `calculate_next_sequence()` to advance
                   the workflow to the next validator (or complete the action if none left).
                4. Update the stored `probability` on the template validation record:
                     new_prob = max(min_allowed, current_probability - ok_impact)



        """
        self.sudo().status = 'done'
        self.env['mail.activity'].search([('user_id', '=', self.user_id.id), ('res_model', '=', 'action.action'), ('res_id', '=', self.action_id.id)]).unlink()
        self.sudo().action_id.calculate_next_sequence()
        
        template_validation = self.sudo().template_validation_id
        min = template_validation.template_template_validation_id.min
        ok_impact = template_validation.template_template_validation_id.ok_impact
        current_probabylity = template_validation.probability
        
        self.sudo().template_validation_id.probability = max(min, current_probabylity-ok_impact)
        
    def set_status_failed(self):
        """
                Mark this validation as failed (rejected).

                Effects / steps:
                1. Set this validation's `status` to 'failed' using sudo().
                2. Remove any mail.activity entries assigned to this validator for the parent action.
                3. Trigger the parent action's `calculate_previous_sequence()` to move the
                   active sequence back to a prior validator (or revert action to todo).
                4. Update the stored `probability` on the template validation record:
                     new_prob = min(max_allowed, current_probability + ko_impact)

              """
        self.sudo().status = 'failed'
        self.env['mail.activity'].search([('user_id', '=', self.user_id.id), ('res_model', '=', 'action.action'), ('res_id', '=', self.action_id.id)]).unlink()
        self.sudo().action_id.calculate_previous_sequence()
        
        template_validation = self.sudo().template_validation_id
        max = template_validation.template_template_validation_id.max
        ko_impact = template_validation.template_template_validation_id.ko_impact
        current_probabylity = template_validation.probability
        
        self.sudo().template_validation_id.probability = min(max, current_probabylity+ko_impact)
        
        
    
