from odoo import api, fields, models, _
import ast


class Goal(models.Model):
    _inherit = 'gamification.goal'

    goal_quest_bonus = fields.Float(string='Quest Bonus', compute="calculate_bonus")
    hours_of_internal_p2_p3 = fields.Float(string="Hours Of Internal P2 P3", readonly=True)
    current_val_with_internal_p2_p3 = fields.Float(string="Current Value with Internal P2 P3", readonly=True)

    @api.depends('goal_quest_bonus')
    def calculate_bonus(self):
        for record in self:
            total_quest_bonus = 0.0
            user_badges = self.env['gamification.badge.user'].search(
                [('user_id', '=', record.user_id.id), ('create_date', '<=', record.end_date)])
            for badge in user_badges:
                total_quest_bonus += badge.badge_id.quest_bonus
            record.goal_quest_bonus = total_quest_bonus

    def compute_hours_of_internal_p2_p3(self):
        """
        This method is used to calculate the hours_of_internal_p2_p3 based on timesheet.
        """
        AnalyticLine = self.env['account.analytic.line']

        for rec in self:
            departure = rec.user_id.employee_id.departure_date
            start = rec.start_date
            end = rec.end_date
            # Apply your condition
            if departure and start <= departure <= end:
                end_date = departure
            else:
                end_date = end
            timesheets = AnalyticLine.search([
                ('user_id', '=', rec.user_id.id),
                ('date', '>=', start),
                ('date', '<=', end_date),
            ])
            internal_timesheets = timesheets.filtered(
                lambda l: l.project_id.project_status_id.code == 'internal_p2p3'
            )
            rec.hours_of_internal_p2_p3 = sum(internal_timesheets.mapped('unit_amount'))

    def compute_current_val_with_internal_p2_p3(self):
        """
        This method is used to calculate the current_val_with_internal_p2_p3 based on hours_of_internal_p2_p3 and current
        """
        for rec in self:
            rec.current_val_with_internal_p2_p3 = rec.hours_of_internal_p2_p3 + rec.current

    def update_goal(self):
        """
        This method is used to inherit and calculate the hours_of_internal_p2_p3 and current_val_with_internal_p2_p3 field
        """
        rec = super(Goal, self).update_goal()
        self.compute_hours_of_internal_p2_p3()
        self.compute_current_val_with_internal_p2_p3()
        return rec

    # TODO : Temperary server action to correct records of goal
    def correct_job_position(self):
        for rec in self:
            skip_ids = [126,127,147,148,162,169,170,175,176,187,208]
            if rec.challenge_id.id in skip_ids:
                continue
            challenge_string = rec.challenge_id.user_domain
            try:
                data = ast.literal_eval(challenge_string)
            except Exception as e:
                continue
            for item in data:
                if isinstance(item, (tuple, list)) and len(item) >= 3:
                    field_name, operator, value = item[0], item[1], item[2]
                    if field_name == "employee_ids.job_id.id" or field_name == "x_studio_employee.job_id.id":
                        job_id = self.env['hr.job'].search([
                            ('id', '=', value),
                            '|', ('active', '=', True), ('active', '=', False)
                        ], limit=1)
                    elif field_name == "x_studio_employee.job_id" or field_name == "x_studio_employee.job_id.name":
                        job_id = self.env['hr.job'].search([
                            ('name', '=', value),
                            '|', ('active', '=', True), ('active', '=', False)
                        ], limit=1)
                    else:
                        continue
                    if job_id:
                        self.env.cr.execute("""UPDATE gamification_goal SET x_studio_previous_job_position = %s WHERE id = %s""",
                                            (job_id.id, rec.id))
                        self.env.cr.commit()
