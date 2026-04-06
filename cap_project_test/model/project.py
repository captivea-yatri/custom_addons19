from odoo import fields, models, api


class Project(models.Model):
    _inherit = 'project.project'

    def action_test_object(self):
        """
        This function is used to open test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_test')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

    def action_execution_test_object(self):
        """
        This function is used to open execution test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_execution_test')
        action['domain'] = [('project_id', '=', self.id)]
        return action

    def action_session_test_object(self):
        """
        This function is used to open session test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_session_test')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

    def action_view_meta_project_req(self):
        tree_view_id = self.env.ref('cap_requirements.view_tree_meta_project_requirement').id
        form_view_id = self.env.ref('cap_requirements.view_form_meta_project_requirement').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meta Project Requirements',
            'view_mode': 'list,form',
            'views': [(tree_view_id, 'list'), (form_view_id, 'form')],
            'res_model': 'meta.project.requirement',
            'domain': [('project_id', '=', self.id)],
            'context': {'create': False, 'delete': False}
        }
