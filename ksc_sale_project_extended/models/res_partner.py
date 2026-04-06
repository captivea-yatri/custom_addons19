# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    # followup_status = fields.Selection(
    #     [('in_need_of_action', 'In need of action'), ('with_overdue_invoices', 'With overdue invoices'),
    #      ('no_action_needed', 'No action needed')],
    #     compute='_compute_followup_status', string='Follow-up Status', store=True, search='_search_status')

    # We have commented this field from V18 because as there is traceback while do accounting related operations
    # and adding timesheets.
    # Now we have considered this field as non-store field our project color computation is now fully working
    # on followup status.

    # total_overdue = fields.Monetary(
    #     compute='_compute_total_due', store=True)
