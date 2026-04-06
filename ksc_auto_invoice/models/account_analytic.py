# coding: utf-8
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalytic(models.Model):
    _inherit = 'account.analytic.line'

    riss_invoice_id = fields.Many2one('account.move',string='Riss Invoice Id')

    @api.ondelete(at_uninstall=False)
    def _unlink_except_invoiced_riss(self):
        """
        Prevent deletion of timesheets that are already invoiced (posted).
        Raises a UserError if any timesheet is linked to a posted invoice.
        """
        if any(line.sudo().riss_invoice_id and line.sudo().riss_invoice_id.state == 'posted' for line in self):
            raise UserError(_('You cannot remove a timesheet that has already been invoiced.'))

    def write(self, values):
        """
        Overrides write to prevent updates on timesheets that are already invoiced.
        Calls _riss_check_can_write before saving changes.
        """
        self._riss_check_can_write(values)
        result = super(AccountAnalytic, self).write(values)
        return result

    def _riss_check_can_write(self, values):
        """
        Checks if timesheets linked to delivered and invoiced lines are being updated.
        Raises an error if protected fields are modified on invoiced timesheets.
        """
        if (self.sudo().filtered(lambda aal: aal.so_line.product_id.invoice_policy == "delivery") and
                self.sudo().filtered(lambda t: t.riss_invoice_id and t.riss_invoice_id.state != 'cancel')):
            if any(field_name in values for field_name in
                   ['unit_amount', 'employee_id', 'project_id', 'task_id', 'so_line', 'amount', 'date']):
                raise UserError(_('You cannot modify timesheet that are already invoiced.'))
