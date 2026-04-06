from odoo import api, fields, models, _

class CronFailureHistory(models.Model):

    _name = "cron.failure.history"
    _description = 'Cron Failure History'
    _rec_name = 'action_name'

    action_name = fields.Char('Scheduled Action Name', readonly=True)
    error_message = fields.Char('Error Message', readonly=True)
    time_of_failure = fields.Datetime(string='Time of failure', readonly=True)
    description = fields.Text('Action Taken',default=None)
    is_solved = fields.Boolean(string='Is Error Solved',default = False)
