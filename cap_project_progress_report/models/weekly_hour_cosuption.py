from odoo import api, fields, models


class WeeklyHourConsumption(models.Model):
    _name = 'weekly.hour.consumption'
    _description = 'Weekly Hour Consumption'

    current_week = fields.Float('Current week (T)')
    week_tminusone = fields.Float('Week (T-1)')
    week_tminustwo = fields.Float('Week (T-2)')
    week_tminusthree = fields.Float('Week (T-3)')
    project_progress_id = fields.Many2one('project.progress','Project Progress')