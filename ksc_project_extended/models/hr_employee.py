from odoo import api, models, fields


class HrJob(models.Model):
    _inherit = 'hr.job'

    team_manager_hours_allocation = fields.Float(string="Team manager hours allocation")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    team_manager_hours_allocation = fields.Float(string="Team manager hours allocation",
                                                 compute='compute_team_manager_hour', store=True,
                                                 groups="hr.group_hr_user")
    internal_project_quota_ids = fields.One2many('internal.project.quotas', 'employee_id', string='Internal Project quotas')

    @api.depends('job_id', 'child_ids', 'child_ids.job_id', 'child_ids.job_id.team_manager_hours_allocation')
    def compute_team_manager_hour(self):
        """Computes and updates the monthly quota of team-manager hours by summing the
team_manager_hours_allocation of all child employees. If a quota record exists
for the manager on the designated internal project, it is updated; otherwise,
a new internal.project.quotas entry is created when hours are allocated."""
        for rec in self:
            if rec.company_id.team_manager_project_id:
                project_quota_id = self.env['internal.project.quotas'].search([
                    ('employee_id', '=', rec.id),
                    ('project_id', '=', rec.company_id.team_manager_project_id.id)])
                total_hours = sum(emp.job_id.team_manager_hours_allocation for emp in rec.child_ids)
                if project_quota_id:
                    project_quota_id.write({'hours_per_month': total_hours})
                elif total_hours > 0:
                    self.env['internal.project.quotas'].create(
                        {'employee_id': rec.id,
                         'project_id': rec.company_id.team_manager_project_id.id,
                         'hours_per_month': total_hours,
                         'name': str(rec.name) + "Internal Project Quota"})

