from odoo import fields, models, api, _


class ProjectDomain(models.Model):
    _inherit = 'project.domain'

    project_manager_time = fields.Float(string='Req Project Manager Time', store=True)
    business_analyst_time = fields.Float(string='Req Business Analyst Time', store=True)
    configurator_time = fields.Float(string='Req Configurator Time', store=True)
    developer_time = fields.Float(string='Req Developer Time', store=True)
    architect_time = fields.Float(string="Req Architect Time", store=True)
    core_time = fields.Float(string="Req Core Time", store=True,
                             help="Core time will be: BA + Conf + Dev + architect time")
    implementation_time = fields.Float(string="Req Implementation Time", store=True,
                                       help="Implementation time will be: Conf + Dev + architect time")
    local_time = fields.Float(string="Req Local Time", store=True,
                              help="Local time  will be: PM + BA")
    offshore_time = fields.Float(string="Req Offshore Time", store=True,
                                 help="Offshore time will be: Conf + dev + architect time")
    estimated_time = fields.Float(string="Req Estimated time", store=True,
                                  help="Estimated time will be: BA + PM + Conf + Dev + architect time.")
    task_estimated_time = fields.Float(string="Task Estimated time", store=True)
    task_passed_time = fields.Float(string="Task passed time", store=True)

    def calculate_project_domain(self):
        """
         This method is used to calculate the role time based on requirement role,
         calculate the task estimated time and task effective hours based on project and domain
        """
        for rec in self:
            project_requirement_ids = self.env['project.requirement'].search(
                [('project_id', '=', rec.project_id.id), ('project_domain_id', '=', rec.id),
                 ('phase_id', '=', rec.phase_id.id), ('role_id', '!=', False), ('used', '!=', 'no')])
            self.calculation_of_time(project_requirement_ids, rec)
            project_task_ids = self.env['project.task'].search([('project_id', '=', rec.project_id.id),
                                                                ('project_domain_id', '=', rec.id)]) #('parent_id', '=', False)
            rec.task_estimated_time = sum(project_task_ids.filtered(lambda t: not t.parent_id).mapped('allocated_hours'))
            rec.task_passed_time = sum(project_task_ids.mapped('effective_hours'))

    def calculation_of_time(self, project_requirement_ids, rec):
        """
        This method is used to calculate of time like pm_time, ba_time, conf_time etc...
        """
        requirement_of_business_analyst = project_requirement_ids.filtered(
            lambda requirement_id: requirement_id.role_id.is_business_analyst)
        rec.business_analyst_time = self.sum_of_advised_estimated_time(requirement_of_business_analyst)
        requirement_of_project_manager = project_requirement_ids.filtered(
            lambda requirement_id: requirement_id.role_id.is_project_manager)
        rec.project_manager_time = self.sum_of_advised_estimated_time(requirement_of_project_manager)
        tasks_of_configurator_time = project_requirement_ids.filtered(
            lambda requirement_id: requirement_id.role_id.is_configurator)
        rec.configurator_time = self.sum_of_advised_estimated_time(tasks_of_configurator_time)
        tasks_of_developer_time = project_requirement_ids.filtered(
            lambda requirement_id: requirement_id.role_id.is_developer)
        rec.developer_time = self.sum_of_advised_estimated_time(tasks_of_developer_time)
        tasks_of_architect_time = project_requirement_ids.filtered(
            lambda requirement_id: requirement_id.role_id.is_architect)
        rec.architect_time = self.sum_of_advised_estimated_time(tasks_of_architect_time)
        rec.estimated_time = rec.business_analyst_time + rec.project_manager_time + rec.configurator_time + rec.developer_time + rec.architect_time
        rec.core_time = rec.business_analyst_time + rec.configurator_time + rec.developer_time + rec.architect_time
        rec.implementation_time = rec.configurator_time + rec.developer_time + rec.architect_time
        rec.local_time = rec.project_manager_time + rec.business_analyst_time
        rec.offshore_time = rec.configurator_time + rec.developer_time + rec.architect_time

    def sum_of_advised_estimated_time(self, requirement_ids):
        """
        This method is used to calculate of estimate time
        """
        return sum(requirement_ids.mapped('estimate_time')) if requirement_ids else 0

    def action_list_task_requirement(self):
        """
        This function is used to open task requirement view
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Requirement',
            'view_mode': 'list,form',
            'res_model': 'project.requirement',
            'domain': [('project_domain_id', '=', self.id), ('default_domain_id', '=', self.default_domain_id.id),
                       ('project_id', '=', self.project_id.id)],
        }

    def remove_unused_domain(self):
        """
        This function will check it there is any project requirement with the same phase and domain or if there is any
        task with the same phase and domain, if there is no task and project requirement it will delete project domain.
        """
        for rec in self:
            project_requirement_ids = self.env['project.requirement'].sudo().search([
                ('project_domain_id', '=', rec.id), ('phase_id', '=', rec.phase_id.id)])
            if not project_requirement_ids:
                task_ids = self.env['project.task'].sudo().search([
                    ('project_id', '=', rec.project_id.id),
                    ('project_domain_id', '=', rec.id), ('active', 'in', [True, False])])
                if not task_ids:
                    rec.unlink()
