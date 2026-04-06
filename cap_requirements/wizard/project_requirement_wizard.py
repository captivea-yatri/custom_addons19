from odoo import fields, models, api
import json


class ProjectRequirementWizard(models.TransientModel):
    _name = 'project.requirement.wizard'
    _description = 'Project Requirement Wizard'

    project_id = fields.Many2one(comodel_name='project.project', string='Project')
    phase_id = fields.Many2one(comodel_name='project.phase', string='Phase', required=True)

    @api.model
    def default_get(self, fields):
        res = super(ProjectRequirementWizard, self).default_get(fields)
        context = self.env.context
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        project_id = self.env[active_model].browse(active_id)
        if project_id:
            res['project_id'] = project_id
        return res

    def action_create_task_from_project(self):
        """
        This method is used to create task based on project requirement phase and project
        """
        context = self.env.context
        project_id = self.env[context.get('active_model')].browse(context.get('active_id'))
        project_requirement_ids = self.env['project.requirement'].search(
            [('phase_id', '=', self.phase_id.id),('used', 'in', [False, 'yes']) ,('project_id', '=', project_id.id)])
        for project_requirement_id in project_requirement_ids:
            vals = {
                'name': project_requirement_id.name,
                'project_id': project_requirement_id.project_id.id,
                'partner_id': project_requirement_id.project_id.partner_id.id,
                'project_domain_id': project_requirement_id.project_domain_id.id,
                'default_phase_id': project_requirement_id.phase_id.id,
                'allocated_hours': project_requirement_id.estimate_time,
                'tag_ids': [(6, 0, project_requirement_id.tag_ids.ids)],
                'role_id': project_requirement_id.role_id.id,
                'description': project_requirement_id.description,
                'project_requirement_id': project_requirement_id.id,
                'help': project_requirement_id.template_requirements_id.help,
                'default_domain_id': project_requirement_id.default_domain_id.id,
            }
            self.find_assignee_id(project_requirement_id, project_id, vals)
            self.env['project.task'].create(vals)

    def find_assignee_id(self, project_requirement_id, project_id, vals):
        """
        This method is used to find and set assignee on the task based on project requirement role
        """
        assignee_ids = False
        if project_requirement_id.role_id.is_developer:
            assignee_ids = project_id.developers_ids
        elif project_requirement_id.role_id.is_configurator:
            assignee_ids = project_id.configurators_ids
        elif project_requirement_id.role_id.is_business_analyst:
            assignee_ids = project_id.business_analyst_ids
        elif project_requirement_id.role_id.is_architect:
            assignee_ids = project_id.architect_ids
        elif project_requirement_id.role_id.is_project_manager:
            assignee_ids = project_id.user_id
        if assignee_ids:
            vals.update({'user_ids': [(4, assignee_id.id) for assignee_id in assignee_ids]})
        elif not assignee_ids and project_id.user_id:
            vals.update({'user_ids': [(4, project_id.user_id.id)]})
