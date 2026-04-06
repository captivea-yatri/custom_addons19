# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    portal_view_all_timesheet = fields.Boolean("View all Timesheet On Portal")
