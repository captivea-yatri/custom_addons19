from odoo import fields, models, api


class TemplateRequirement(models.Model):
    _inherit = 'template.requirement'

    def action_template_object(self):
        """
        This function is used to open template test view
        """
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_test.action_template_test')
        action['domain'] = [('template_requirement_id', '=', self.id)]
        action['context'] = {
            'default_template_requirement_id': self.id,  # Set the default value
        }
        return action
