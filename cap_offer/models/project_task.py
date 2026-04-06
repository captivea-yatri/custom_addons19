from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    restrict_time = fields.Boolean(related='task_id.offer_id.restrict_time')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    offer_id = fields.Many2one('offer.offer', string='So Offer', related='project_id.offer_id')
    restrict_time = fields.Boolean(related='project_id.offer_id.restrict_time')

    @api.constrains('allocated_hours', 'effective_hours')
    def _check_planned_hours(self):
        """
        Arise validation when allocated hours is less than Hours Spent
        """
        for task in self:
            if (task.offer_id and task.offer_id.restrict_time and task.project_id.company_id.allow_offer_date and
                    task.create_date.date() >= task.project_id.company_id.allow_offer_date and
                    task.allocated_hours < task.effective_hours):
                raise ValidationError('As offer on project is with restricted time. '
                                      'You can not log more time that what is allocated on task!')

    def _check_task(self):
        """
        Arise ValidationError when create new task if offer restrict time == True.
        """
        for task in self:
            if not self._context.get('link_so_project', False) and self._context.get('task_restricted', False):
                if task.offer_id.restrict_time:
                    raise ValidationError('Manual task can not be created, on offer with Restrict Time : True')

    @api.constrains('project_id')
    def restricted_task(self):
        for rec in self:
            if (rec.project_id.company_id.allow_offer_date and
                    rec.create_date.date() >= rec.project_id.company_id.allow_offer_date):
                if not rec._context.get('link_so_project', False):
                    rec.with_context(task_restricted=True)._check_task()

    def _send_invite_for_task(self, partner_ids, send_mail):
        if partner_ids:
            invite_wizard = self.env['mail.wizard.invite'].sudo().create({
                'res_model': 'project.task',
                'res_id': self.id,
                'partner_ids': [(4, partner_id.id) for partner_id in partner_ids],
                'message': _('You have been invited to follow this Task: %s') % self.name,
                'notify': send_mail,
            })
            invite_wizard.sudo().add_followers()

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ProjectTask, self).create(vals_list)
        for rec in res:
            if (rec.create_date and rec.project_id.company_id.allow_offer_date and
                    rec.create_date.date() >= rec.project_id.company_id.allow_offer_date):
                rec.with_context(task_restricted=True)._check_task()
        # if res.project_id:
        #     pm_of_customer = res.project_id.signatory_progress_report_partner_id
        #     if pm_of_customer:
        #         res._send_invite_for_task(partner_ids=pm_of_customer, send_mail=True)
        return res

    @api.model
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        for rec in self:
            if (rec.create_date and rec.project_id.company_id.allow_offer_date and
                    rec.create_date.date() >= rec.project_id.company_id.allow_offer_date):
                if vals.get('sale_line_id'):
                    rec.with_context(task_restricted=True)._check_task()
        return res
