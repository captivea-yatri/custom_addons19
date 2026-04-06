from odoo import fields, models, api
from datetime import timedelta, datetime
from pytz import UTC, timezone
from collections import namedtuple
from odoo.exceptions import ValidationError

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


class ProjectPlanningWizard(models.TransientModel):
    _name = 'project.planning.wizard'
    _description = 'Project Planning Wizard'

    project_id = fields.Many2one(comodel_name='project.project', string='Project',
                                 default=lambda self: self.env.context.get('active_id'))
    phase_id = fields.Many2one(comodel_name='project.phase', string='Phase', required=True)
    weekly_capacity = fields.Integer(string="Weekly Capacity", related='phase_id.weekly_capacity')
    planning_start_date = fields.Date(string="Planning Start Date", related='phase_id.planning_start_date')

    def float_to_time(value):
        """Convert float hours (e.g. 3.5) to 'HH:MM' string."""
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def calculate_planning_hours(self):
        if self.phase_id.weekly_capacity <= 0:
            raise ValidationError("The weekly capacity for the phase should be greater than zero!")
        task_ids = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id), ('default_phase_id', '=', self.phase_id.id),
             ('is_functional_task', '=', True), ('stage_id.is_done_for_captivea', '=', False)])
        task_ids = task_ids.sorted(
            key=lambda t: (t.project_domain_id.sequence,
                           t.project_requirement_id.sequence if t.project_requirement_id else t.id))
        daily_capacity = self.phase_id.weekly_capacity / 5
        planning_start_date = self.phase_id.planning_start_date
        if planning_start_date and planning_start_date > fields.Date.today():
            # Combine the planning start date with the current time
            current_date = datetime.combine(planning_start_date, datetime.now().time())
        else:
            current_date = datetime.now()
        # Set Current capacity as daily capacity
        current_capacity = daily_capacity

        # Check public holiday and weekends
        current_date = self.check_non_working_days(current_date)

        for task in task_ids:
            task_hours = task.allocated_hours

            # Case when current capacity is enough for the whole task
            if current_capacity >= task_hours:
                task.with_context({'fsm_mode': True}).write({
                    'planned_date_begin': current_date,
                    'date_deadline': current_date
                })
                current_capacity -= task_hours  # Deduct task hours from current capacity
            else:
                # Calculate how many additional days are needed for the remaining hours
                remaining_hours = task_hours
                task_start_date = current_date

                while remaining_hours > 0:
                    if current_capacity > 0:
                        if remaining_hours <= current_capacity:
                            task.with_context({'fsm_mode': True}).write(
                                {'planned_date_begin': task_start_date, 'date_deadline': current_date})
                            current_capacity -= remaining_hours  # Deduct the remaining hours
                            remaining_hours = 0  # Task is done
                        else:
                            # Partial day allocation, move to next day
                            remaining_hours -= current_capacity
                            current_capacity = 0

                    # If capacity is exhausted or task isn't finished, move to the next day
                    if current_capacity == 0 and remaining_hours > 0:
                        current_date += timedelta(days=1)
                        current_date = self.check_non_working_days(current_date)  # Adjust for holidays/weekends
                        current_capacity = daily_capacity  # Reset capacity for the next day

            # Move to the next day if the current capacity is 0 (means the day is finished)
            if current_capacity == 0:
                current_date += timedelta(days=1)
                current_date = self.check_non_working_days(current_date)
                current_capacity = daily_capacity  # Reset capacity for the new day

    def check_non_working_days(self, date):
        # Check if it's a weekend
        while date.weekday() >= 5:
            date = date + timedelta(days=1)
        # Check if it's a public holiday
        # We need the employee to check the public holidays of the project's company.
        employee_id = self.env['hr.employee'].search([('company_id', '=', self.project_id.company_id.id)], limit=1)
        # Here, we convert the current_date to the start_date and end_date, similar to how it is done for leave,
        # to ensure accurate calculations, just like in the base implementation.
        # We follow the same scenario as the default base method _compute_date_from_to()
        domain = [('calendar_id', '=', self.project_id.company_id.resource_calendar_id.id), ('resource_id', '=', False)]
        attendances = self.env['resource.calendar.attendance'].read_group(domain,
                                                                          ['ids:array_agg(id)',
                                                                           'hour_from:min(hour_from)',
                                                                           'hour_to:max(hour_to)',
                                                                           'week_type', 'dayofweek', 'day_period'],
                                                                          ['week_type', 'dayofweek', 'day_period'],
                                                                          lazy=False)
        attendances = sorted([DummyAttendance(group['hour_from'], group['hour_to'], group['dayofweek'],
                                              group['day_period'], group['week_type']) for group in attendances],
                             key=lambda att: (att.dayofweek, att.day_period != 'morning'))
        default_value = DummyAttendance(0, 0, 0, 'morning', False)
        attendance_from = next((att for att in attendances if int(att.dayofweek) >= date.date().weekday()),
                               attendances[0] if attendances else default_value)
        attendance_to = next(
            (att for att in reversed(attendances) if int(att.dayofweek) <= date.date().weekday()),
            attendances[-1] if attendances else default_value)
        date_from = self._get_start_or_end_from_attendance_for_calc(attendance_from.hour_from, date.date())
        date_to = self._get_start_or_end_from_attendance_for_calc(attendance_to.hour_to, date.date())
        # Use base default's method :_get_work_days_data_batch()
        result = employee_id._get_work_days_data_batch(date_from, date_to, domain=domain)
        for calendar_resource_id, data in result.items():
            days_value = data.get('days')
            # If days_value = 0 then it is public holiday
            if days_value == 0:
                date = date + timedelta(days=1)
                return self.check_non_working_days(date)
        return date

    def _get_start_or_end_from_attendance_for_calc(self, hour, date):
        """
        This function is used to get start or end from attendance with timezone.
        """
        hour = float_to_time(float(hour))
        holiday_tz = timezone(self.project_id.company_id.resource_calendar_id.tz or 'UTC')
        return holiday_tz.localize(datetime.combine(date, hour)).astimezone(UTC).replace(tzinfo=None)
