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
        self = self.with_context(link_so_project=True)
        context = self.env.context
        project_id = self.env[context.get('active_model')].browse(context.get('active_id'))
        if (project_id.company_id.allow_offer_date and
                project_id.create_date.date() >= project_id.company_id.allow_offer_date):
            project_requirement_ids = self.env['project.requirement'].search(
                [('phase_id', '=', self.phase_id.id), ('used', 'in', [False, 'yes']),
                 ('project_id', '=', project_id.id)])
            for project_requirement_id in project_requirement_ids:
                sale_line_ids = project_id.sale_order_line_ids.filtered(
                    lambda r: project_requirement_id.default_domain_id.id in r.product_id.default_domain_ids.ids)
                if project_requirement_id.default_domain_id.id in sale_line_ids.product_id.default_domain_ids.ids:
                    self.create_task_and_task_test(project_requirement_id, sale_line_ids[0], project_id)
                else:
                    self.create_task_and_task_test(project_requirement_id, project_id.sale_line_id, project_id)
        else:
            return super().action_create_task_from_project()

    def prepare_task_vals(self, project_requirement_id, sale_line_id):
        vals = {
            'name': project_requirement_id.name,
            'project_id': project_requirement_id.project_id.id,
            'partner_id': project_requirement_id.project_id.partner_id.id,
            'project_domain_id': project_requirement_id.project_domain_id.id,
            'default_phase_id': project_requirement_id.phase_id.id,
            'allocated_hours': project_requirement_id.estimate_time * sale_line_id.product_uom_qty if project_requirement_id.default_domain_id.id in sale_line_id.product_id.default_domain_ids.ids else project_requirement_id.estimate_time,
            'sale_line_id': sale_line_id.id,
            'role_id': project_requirement_id.role_id.id,
            'description': project_requirement_id.description,
            'project_requirement_id': project_requirement_id.id,
            'tag_ids': [(6, 0, project_requirement_id.tag_ids.ids)],
            'help': project_requirement_id.template_requirements_id.help,
            'default_domain_id': project_requirement_id.default_domain_id.id,
        }
        return vals

    def prepare_task_test_vals(self,project_requirement_id, template_test_id,task_id):
        vals = {
            'name': project_requirement_id.name,
            'template_test_id': template_test_id.id,
            'project_domain_id': project_requirement_id.project_domain_id.id,
            'project_id': project_requirement_id.project_id.id,
            'task_id': task_id.id,
            'tag_ids': [(6, 0, project_requirement_id.project_id.tag_ids.ids)],
            'description': template_test_id.description
        }
        return vals

    def search_template_test(self,project_requirement_id):
        return self.env['template.test'].search(
                        [('template_requirement_id', '=', project_requirement_id.template_requirements_id.id)])

    def create_task_and_task_test(self, project_requirement_id, sale_line_id, project_id):
        vals = self.prepare_task_vals(project_requirement_id, sale_line_id)
        self.find_assignee_id(project_requirement_id, project_id, vals)
        task_id = self.env['project.task'].create(vals)
        template_test_ids = self.search_template_test(project_requirement_id)
        for template_test_id in template_test_ids:
            vals = self.prepare_task_test_vals(project_requirement_id, template_test_id, task_id)
            self.env['test.test'].create(vals)
