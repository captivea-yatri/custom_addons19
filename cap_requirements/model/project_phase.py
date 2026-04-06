from odoo import fields, models, api


class ProjectPhase(models.Model):
    _inherit = 'project.phase'

    weekly_capacity = fields.Integer(string="Weekly Capacity", default=20)
    planning_start_date = fields.Date(string="Planning Start Date", tracking=True)
