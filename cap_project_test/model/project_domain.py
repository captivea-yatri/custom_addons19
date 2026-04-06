from odoo import fields, models, api


class ProjectDomain(models.Model):
    _inherit = 'project.domain'

    def action_list_task(self):
        """
        This function is used to open task view
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Task',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('project_id', '=', self.project_id.id), ('project_domain_id', '=', self.id),
                       ('default_phase_id', '=', self.phase_id.id),
                       ('default_domain_id', '=', self.default_domain_id.id)],
        }

    def action_domain_test_object(self):
        """
        This function is used to open test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_test')
        action['domain'] = [('project_id', '=', self.project_id.id),
                            ('project_domain_id', '=', self.id)]
        return action

    def action_domain_execution_test_object(self):
        """
        This function is used to open execution test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_execution_test')
        action['domain'] = [('project_id', '=', self.project_id.id), ('domain_id', '=', self.id)]
        return action
