# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command,_
from odoo.exceptions import ValidationError,UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    time_credit_ids = fields.Many2many('time.credit', 'credit_move_line_rel', 'line_id', 'credit_id',compute='_compute_time_credit_ids',
                                       string='Related Time Credits', copy=False, store=True)

    @api.depends('move_id.state', 'parent_state')
    def _compute_time_credit_ids(self):
        ''' Compute related time credits for the account move line. '''
        for record in self:
            if not record.time_credit_ids:
                if record.move_id.move_type == 'out_invoice' and record.move_id.time_credit_id:
                    record.time_credit_ids = [(4, record.move_id.time_credit_id.id)]

    def unlink(self):
        ''' Raise ValidationError if time credits are linked with the journal item being deleted. '''
        # Custom logic before unlinking records
        for record in self:
            record._compute_time_credit_ids()
            if record.move_id.move_type == 'out_invoice' and record.time_credit_ids:
                raise ValidationError('Time credits are linked with this journal item')
        return super(AccountMoveLine, self).unlink()

    def reconcile(self):
        ''' Update time credit synchronization for related partners after reconciliation. '''
        results = super(AccountMoveLine, self).reconcile()
        for rec in self:
            if rec.partner_id:
                rec.partner_id.update_time_credit_synchronization_for_partner(rec.partner_id)
        return results

    def remove_move_reconcile(self):
        ''' Update time credit synchronization for related partners after removing reconciliation. '''
        res = super(AccountMoveLine, self).remove_move_reconcile()
        for rec in self:
            if rec.partner_id:
                rec.partner_id.update_time_credit_synchronization_for_partner(rec.partner_id)
        return res
