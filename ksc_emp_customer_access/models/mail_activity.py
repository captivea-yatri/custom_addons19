from odoo import models, api


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model_create_multi
    def create(self, vals_list):
        activities = self.env[self._name]
        for vals in vals_list:
            if vals.get("res_model") == "approval.request" or (
                    vals.get("res_model_id")
                    and self.env["ir.model"].sudo().browse(vals["res_model_id"]).model == "approval.request"
            ):
                act = super(MailActivity, self.with_context(mail_activity_quick_update=True)).create([vals])
            else:
                act = super(MailActivity, self).create([vals])

            for rec in act:
                rec.create_activity_for_manager()

            activities |= act
        return activities

    def create_activity_for_manager(self):
        if self.res_model_id.id != self.env.ref(
                'hr_appraisal.model_hr_appraisal').id and self.res_model_id.id != self.env.ref(
            'hr_holidays.model_hr_leave').id and self.res_model_id.id != self.env.ref(
            'hr_expense.model_hr_expense').id and self.res_model_id.id != self.env.ref(
            'approvals.model_approval_request').id :
            if self.user_id.employee_id and self.user_id.employee_id.parent_id and self.user_id.employee_id.parent_id.user_id:
                leave_ids = self.env['hr.leave'].sudo().search(
                    [('user_id', '=', self.user_id.id), ('state', '=', 'validate'),
                     ('request_date_from', '<=', self.create_date.date()),
                     ('request_date_to', '>=', self.create_date.date())])
                if leave_ids:
                    activity_values = {
                        'res_model_id': self.res_model_id.id,
                        'res_id': self.res_id,
                        'activity_type_id': self.activity_type_id.id,
                        'date_deadline': self.date_deadline,
                        'summary': self.summary,
                        'note': self.note,
                        'user_id': self.user_id.employee_id.parent_id.user_id.id,
                    }
                    return self.copy(default=activity_values)
