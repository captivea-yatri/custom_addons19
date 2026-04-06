# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

# TODO: check this code because blocked field is removed in V18
    # @api.constrains('blocked')
    # def _check_block_line(self):
    #     """
    #     This function is used to process color code for project and its task.
    #     When there is any change in blocked field it will compute color for project and task.
    #     This will be related to partner of particular invoice.
    #     """
    #     for rec in self:
    #         main_partner_id = rec.move_id.partner_id.parent_id and \
    #                           rec.move_id.partner_id.parent_id or rec.move_id.partner_id
    #         company_ids = self.env['res.company'].sudo().search([])
    #         if main_partner_id and main_partner_id.id not in company_ids.mapped('partner_id').ids:
    #             project_ids = self.env['project.project'].search([('partner_id', 'child_of', main_partner_id.ids)])
    #             if project_ids:
    #                 main_partner_id.sudo()._compute_followup_status()
    #                 project_ids.sudo().compute_project_color_remaining_hours()
    #                 project_ids.mapped('task_ids').sudo().compute_task_color()


# TODO: As the bellow code was slowdowning the execution for the invoice confirmation we have commented the code.
# This may will not have major issue and task color compute will work from scheduled action.

# class AccountMove(models.Model):
#     _inherit = 'account.move'

    # @api.constrains('state', 'invoice_date_due')
    # def _check_invoice_state(self):
    #     """
    #     This function is used to process color code for project and its task.
    #     When the state and due date gets reflected it will compute color for project and task.
    #     This will be related to partner of particular invoice.
    #     """
    #     for rec in self.filtered(lambda move: move.move_type == 'out_invoice'):
    #         main_partner_id = rec.partner_id.parent_id and rec.partner_id.parent_id or rec.partner_id
    #         project_ids = self.env['project.project'].search([('partner_id', 'child_of', main_partner_id.ids)])
    #         if project_ids:
    #             main_partner_id._compute_for_followup()
    #             project_ids.compute_project_color()
    #             project_ids.mapped('task_ids').compute_task_color()


