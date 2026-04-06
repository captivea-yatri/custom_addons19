from odoo import fields, models, api
from datetime import date, timedelta

import random

class ActionTemplate(models.Model):
    _name = 'action.template'
    _description = 'Action Template'
    
    name = fields.Char(string='Name', compute='_compute_name')
    
    custom_name = fields.Char(string='Custom Name')
    start_date = fields.Date('Start Date')
    meta_template_id = fields.Many2one('action.meta.template', string='Action Meta Template')
    user_id = fields.Many2one('res.users', string='User')
    substitute_ids = fields.One2many('action.template.substitute', 'template_id', string="Substitutes")
    action_ids = fields.One2many('action.action', 'template_id', string="Actions")
    validation_ids = fields.One2many('action.template.validation', 'template_id', string="Validations")

    company_id = fields.Many2one('res.company', string='Company')
    
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Frequency')

    day_of_month = fields.Integer(string='Day of month')
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ])
    deadline_in_days = fields.Integer(string='DeadLine in days')
    score_impact = fields.Integer(string='Score Impact')
    
    override_description = fields.Boolean(string='Override Description')
    description = fields.Html(string='Description', compute='_compute_description', store=True )
    
    template_template_id = fields.Many2one('action.template.template', string="Template Template")


    @api.depends('meta_template_id')
    def _compute_description(self):
        for at in self:
            if not at.override_description:
                at.description = at.meta_template_id.description
                
    def _compute_name(self):
        """
            Compute the display name for the template.
            Priority:
                 1. If a `meta_template_id` is set, use its name.
                 2. Otherwise use `custom_name`.
        """
        for at in self:
            if at.meta_template_id.id != False:
                at.name = at.meta_template_id.name
            else:
                at.name = at.custom_name

    def get_responsable(self, user, substitute_ids, frequency):
        """
         Determine the responsible user for a new action instance.
         Behavior:
               - For 'daily' frequency: check whether the primary user's related hr.employee
                 record(s) indicate absence (field `is_absent`).
                 If absent, iterate substitutes in increasing `sequence` order and pick
                 the first substitute whose hr.employee is not absent.
               - If the selected responsible remains the original user, returns False (meaning
                 "no substitute found" in this implementation).
        """
        responsible_user_id = user.id
        if frequency == "daily":
            look_for_substitute = False
            for employee in self.env['hr.employee'].search([('user_id', '=', responsible_user_id)]):
                if employee.is_absent:
                    look_for_substitute = True
            
            if look_for_substitute:
                for substitute in substitute_ids.sorted(key=lambda r: r.sequence):
                    can_be_substitute = True
                    for employee in self.env['hr.employee'].search([('user_id', '=', substitute.user_id.id)]):
                        if employee.is_absent:
                            can_be_substitute = False
                    if can_be_substitute:
                        responsible_user_id = substitute.user_id.id
                if responsible_user_id == user.id:
                    responsible_user_id = False
                
        return responsible_user_id
                                    

    def reset_template_template(self):
        """
            Copy substitutes and validations from the linked `template_template_id`.
            Behavior:
                - If a `template_template_id` is set, it removes current `substitute_ids`
                  and `validation_ids` and then clones the substitutes and validations from
                  the template template into this action template.
                - The method writes the new sets using ORM commands (0,0,data) to create lines.
            Side effects:
                - Deletes existing substitute and validation records for this template.
                - Creates new substitute and validation records based on the template template.
        """
        for template in self:
            if template.template_template_id.id != False:
                template.substitute_ids.unlink()
                template.validation_ids.unlink()
                
                substitute_ids = []
                for substitute in template.template_template_id.substitute_ids:
                    substitute_data = {
                                        'template_id' : template.id,
                                        'user_id' : substitute.user_id.id,
                                        'sequence' : substitute.sequence,
                                    }
                    substitute_ids.append((0, 0, substitute_data))
                    
                validation_ids = []
                for validation in template.template_template_id.validation_ids:
                    validation_data = {
                                        'template_id' : template.id,
                                        'template_template_validation_id' : validation.id,
                                        'user_id' : validation.user_id.id,
                                        'probability' : validation.start,
                                        'sequence' : validation.sequence,
                                    }
                    validation_ids.append((0, 0, validation_data))
                
                update_values = {
                    'substitute_ids' : substitute_ids,
                    'validation_ids' : validation_ids,
                }
                template.write(update_values)

    def generate_action(self):
        """
            Generate action instances from all action templates.

               This method iterates every Action Template and — when conditions pass —
               creates a corresponding `action.action` record for the current date.

               High-level steps:
               - Compute `today`, `tomorrow`, first day of period markers.
               - For each template:
                 - Check start date and active status.
                 - Verify no existing open action for this template.
                 - Check calendar leaves/public holidays.
                 - Enforce frequency rules (daily/weekly/monthly/yearly).
                 - Evaluate the linked meta template (call evaluate()).
                 - Build validation lines (selected probabilistically).
                 - Determine responsible user (apply substitutes when needed).
                 - Create `action.action` with computed values.
        """
        template_actions = self.env['action.template'].search([])
        today = date.today()
        tomorrow =  today + timedelta(days=1)
        first_day_of_week = today - timedelta(days=today.weekday())
        first_day_of_month = today.replace(day=1)
        first_day_of_year = first_day_of_month.replace(month=1)
        day_of_month = today.day
        month = today.month
        
        for template_action in template_actions:
            
            if template_action.start_date == False or template_action.start_date <= today:
                search_request = [
                    ('template_id', '=', template_action.id),
                    ('status', 'in', ["todo", "invalidation"]),
                ]
                
                domain = [
                    ('resource_id', '=', False),
                    ('company_id', '=', template_action.company_id.id),
                    ('date_from', '<=', today),
                    ('date_to', '>=',tomorrow),
                    ('calendar_id', '=', False),
                ]

                is_public_holiday = False  
                if self.env['resource.calendar.leaves'].search_count(domain) > 0:
                    is_public_holiday = True
                
                if self.env['action.action'].search_count(search_request) == 0 and today.weekday() < 5 and is_public_holiday == False:
                    to_create = True
                    if template_action.frequency == "daily":
                        if self.env['action.action'].search_count([('template_id', '=', template_action.id), ('date', '=', today)]) > 0:
                            to_create = False
                    elif template_action.frequency == "weekly":
                        if self.env['action.action'].search_count([('template_id', '=', template_action.id), ('date', '>=', first_day_of_week)]) > 0:
                            to_create = False
                    elif template_action.frequency == "Monthly":
                        if self.env['action.action'].search_count([('template_id', '=', template_action.id), ('date', '>=', first_day_of_month)]) > 0 or day_of_month < template_action.day_of_month:
                            to_create = False
                    elif template_action.frequency == "yearly":
                        if self.env['action.action'].search_count([('template_id', '=', template_action.id), ('date', '>=', first_day_of_year)]) > 0 :
                            to_create = False
                        if month < int(template_action.month):
                            to_create = False
                        elif month == int(template_action.month) and day_of_month < template_action.day_of_month:
                            to_create = False
                    
                    if to_create == True:
                        
                        if template_action.meta_template_id.evaluate(template_action.company_id.id) != True:
                            validation_ids = []
                            
                            for validation in template_action.validation_ids:
                                
                                responsible_user_id = self.get_responsable(validation.user_id, [], template_action.frequency)
                                if responsible_user_id != False:
                                    if random.randrange(1,100) <= validation.probability:
                                        data_validaton = {
                                            'template_validation_id' : validation.id,
                                            'user_id' : responsible_user_id,
                                            'sequence' : validation.sequence,
                                            'status' : 'tovalidate',
                                        }
                                        validation_ids.append((0, 0, data_validaton))
                            
                            
                            responsible_user_id = self.get_responsable(template_action.user_id, template_action.substitute_ids, template_action.frequency)
                            if responsible_user_id != False:
                                create_values = {
                                    'date' : today,
                                    'deadline' : today + timedelta(days=template_action.deadline_in_days),
                                    'template_id': template_action.id,
                                    'status' : 'todo',
                                    'user_id' : responsible_user_id,
                                    'validation_ids': validation_ids,
                                    'company_id': template_action.company_id.id,
                                    'scoreimpact' : template_action.score_impact,
                                    'description' : template_action.description,
                                }
                                self.env['action.action'].create(create_values)
                
                
