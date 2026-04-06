from odoo import api, fields, models, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    project_domain_id = fields.Many2one(comodel_name='project.domain', related='task_id.project_domain_id', store=True,
                                        string='Domain')
    default_phase_id = fields.Many2one(comodel_name='project.phase', related='task_id.default_phase_id', store=True,
                                       string='Phase')

    def create(self, vals):
        """
         Overrides create to automatically assign the employee’s user to the appropriate
         project role (BA, Configurator, Developer, Architect) based on the task's role.
         Ensures the user is added to the project role lists only if not already assigned.
         """
        res = super(AccountAnalyticLine, self).create(vals)
        for rec in res:
            if rec.employee_id:
                if rec.task_id.role_id.is_business_analyst and rec.employee_id.user_id not in rec.project_id.business_analyst_ids:
                    rec.project_id.sudo().business_analyst_ids = [(4, u.id) for u in rec.employee_id.user_id]
                elif rec.task_id.role_id.is_configurator and rec.employee_id.user_id not in rec.project_id.configurators_ids:
                    rec.project_id.sudo().configurators_ids = [(4, u.id) for u in rec.employee_id.user_id]
                elif rec.task_id.role_id.is_developer and rec.employee_id.user_id not in rec.project_id.developers_ids:
                    rec.project_id.sudo().developers_ids = [(4, u.id) for u in rec.employee_id.user_id]
                elif rec.task_id.role_id.is_architect and rec.employee_id.user_id not in rec.project_id.architect_ids:
                    rec.project_id.sudo().architect_ids = [(4, u.id) for u in rec.employee_id.user_id]
        return res
