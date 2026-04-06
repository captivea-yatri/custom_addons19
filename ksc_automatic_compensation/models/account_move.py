from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = "account.move"

    is_inv_bill_found = fields.Boolean('invoice/bill found', compute='_compute_is_invoice_bill_found')

    def get_inv_bill_status(self):
        domain = [('state', '=', 'posted'),
                  ('amount_residual', '>', 0.0),
                  ('move_type', '=', 'in_invoice') if self.move_type == 'out_invoice' else (
                      'move_type', '=', 'out_invoice'), '|', '|', ('partner_id', '=', self.partner_id.id),
                  ('partner_id', '=', self.partner_id.parent_id.id),
                  ('partner_id.parent_id', '=', self.partner_id.id),
                  ('company_id', '=', self.company_id.id)]
        if self.partner_id.parent_id:
            domain.insert(3, '|')
            domain.append(('partner_id.parent_id', '=', self.partner_id.parent_id.id))
        return domain

    def _compute_is_invoice_bill_found(self):
        for rec in self:
            domain = rec.get_inv_bill_status()
            inv_bill_search = rec.env['account.move'].search(domain)
            rec.is_inv_bill_found = True if inv_bill_search else False

    def button_compensate(self):
        vals = {
            'amount': self.amount_residual,
        }
        domain = self.get_inv_bill_status()
        if self.move_type == 'out_invoice':
            v_bill_list = []
            bill_search = self.env['account.move'].search(domain)
            for bill in bill_search:
                v_bill_list.append((0, 0, {'currency_id': self.currency_id.id, 'inv_bill_number': bill.name,
                                           'inv_bill_id': bill.id, 'inv_bill_amount': bill.amount_residual,
                                           'is_partial_paid': True if bill.payment_state == 'partial' else False}))
            vals.update({'invoice_bill_ids': v_bill_list})
        if self.move_type == 'in_invoice':
            inv_bill_list = []
            inv_search = self.env['account.move'].search(domain)
            for inv in inv_search:
                inv_bill_list.append((0, 0,
                                      {'currency_id': self.currency_id.id, 'inv_bill_number': inv.name,
                                       'inv_bill_id': inv.id, 'inv_bill_amount': inv.amount_residual,
                                       'is_partial_paid': True if inv.payment_state == 'partial' else False}))
            vals.update({'invoice_bill_ids': inv_bill_list})
        create_wiz = self.env['ksc.auto.compensate'].create(vals)
        if create_wiz:
            for inv_bill in create_wiz.invoice_bill_ids:
                inv_bill.compensate_id = create_wiz.id
        return {
            'name': _('Automatic Compensate'),
            'view_mode': 'form',
            'res_model': 'ksc.auto.compensate',
            'res_id': create_wiz.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
