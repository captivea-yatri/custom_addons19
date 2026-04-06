# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MarkCustomerLost(models.TransientModel):
    _name = 'mark.customer.lost'
    _description = 'Mark Customer Lost'

    partner_id = fields.Many2one('res.partner', 'Partner')
    lost_date = fields.Date('Lost Date')
    lost_reason = fields.Text('Lost Reason')

    @api.model
    def default_get(self, fields):
        """Getting default values of fields through active record"""
        res = super(MarkCustomerLost, self).default_get(fields)
        res_id = self.env.context.get('active_id')
        res_model = self.env.context.get('active_model')
        if res_id and res_model == 'res.partner':
            res.update({
                'partner_id': res_id,
            })
        return res

    def do_validate(self):
        # TODO: need to check with DK Sir & Seb, I think we need to update status of contacts as not_customer or something.
        self.partner_id.write({'no_customer_since': self.lost_date, 'status': 'old_customer'})
        self.env['mail.message'].create({'date': fields.Date.today(),
                                         'model': 'res.partner',
                                         'res_id': self.partner_id.id,
                                         'record_name': self.partner_id.name,
                                         'author_id': self.env.user.partner_id.id,
                                         'message_type': 'comment',
                                         'body': str(self.lost_reason + " <br> Not a customer anymore since : " +
                                                     str(self.lost_date)),
                                         })
