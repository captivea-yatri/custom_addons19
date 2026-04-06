from odoo import fields, models, api


class Phase(models.Model):
    _inherit = 'project.phase'

    def action_list_task(self):
        """
        This function is used to open task view
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Task',
            'view_mode': 'list,form',
            'res_model': 'project.task',
            'domain': [('default_phase_id', '=', self.id)],
        }

    def action_phase_test_object(self):
        """
        This function is used to open test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_test')
        action['domain'] = [('project_id', '=', self.project_id.id)]
        return action

    def action_phase_execution_test_object(self):
        """
        This function is used to open execution test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_execution_test')
        action['domain'] = [('phase_id', '=', self.id)]
        return action
