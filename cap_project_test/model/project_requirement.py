from odoo import fields, models, api


class ProjectRequirement(models.Model):
    _inherit = 'project.requirement'

    def action_project_object(self):
        """
        This function is used to open test form and show template requirements related records
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_test')
        action['domain'] = [('template_test_id.template_requirement_id', '=', self.template_requirements_id.id),
                            ('project_id', '=', self.project_id.id)]
        return action
