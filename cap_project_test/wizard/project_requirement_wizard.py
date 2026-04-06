from odoo import fields, models, api,_
from odoo.exceptions import ValidationError

class ProjectRequirementWizard(models.TransientModel):
    _inherit = 'project.requirement.wizard'

    def action_create_task_from_project(self):
        """
        This method is override to requirement method and it is used to
        - create test based on template test template requirement and
        - create task based on project requirement
        """
        context = self.env.context
        project_id = self.env[context.get('active_model')].browse(context.get('active_id'))
        project_requirement_ids = self.env['project.requirement'].search(
            [('phase_id', '=', self.phase_id.id), ('used', 'in', [False, 'yes']),
             ('project_id', '=', project_id.id)])
        for project_requirement_id in project_requirement_ids:
            vals = {
                'name': project_requirement_id.name,
                'project_id': project_requirement_id.project_id.id,
                'partner_id': project_requirement_id.project_id.partner_id.id,
                'project_domain_id': project_requirement_id.project_domain_id.id,
                'default_phase_id': project_requirement_id.phase_id.id,
                'allocated_hours': project_requirement_id.estimate_time,
                'role_id': project_requirement_id.role_id.id,
                'tag_ids': [(6, 0, project_requirement_id.tag_ids.ids)],
                'description': project_requirement_id.description,
                'project_requirement_id': project_requirement_id.id,
                'help': project_requirement_id.template_requirements_id.help,
                'default_domain_id': project_requirement_id.default_domain_id.id,
            }
            self.find_assignee_id(project_requirement_id, project_id, vals)
            task_id = self.env['project.task'].create(vals)
            template_test_ids = self.env['template.test'].search(
                [('template_requirement_id', '=', project_requirement_id.template_requirements_id.id)])
            for template_test_id in template_test_ids:
                self.env['test.test'].create({
                    'name': project_requirement_id.name,
                    'template_test_id': template_test_id.id,
                    'project_domain_id': project_requirement_id.project_domain_id.id,
                    'project_id': project_requirement_id.project_id.id,
                    'task_id': task_id.id,
                    'tag_ids': [(6, 0, template_test_id.tag_ids.ids)],
                    'description': template_test_id.description
                })
