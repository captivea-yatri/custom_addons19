from odoo import fields, models


class MetaProjectRequirement(models.Model):
    _name = 'meta.project.requirement'
    _description = 'Meta Project Requirement'

    name = fields.Char(string="Name")
    project_id = fields.Many2one('project.project')
    meta_template_requirement_id = fields.Many2one('meta.template.requirement')
    calculation_formula = fields.Text(string="Calculation Formula", default="""# Available variables:
#-------------------------------

# PM_TIME: Project Manager Time
# BA_TIME: Business Analyst Time
# CONF_TIME: Configurator Time
# DEV_TIME: Developer Time
# ARCH_TIME: Architecture Time

# Note: returned value have to be set in the variable 'result'

result = BA_TIME * 0.10
    """)

    def action_view_project_requirement(self):
        tree_view_id = self.env.ref('cap_requirements.project_requirement_tree_view_for_analysis').id
        form_view_id = self.env.ref('cap_requirements.project_requirement_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Requirement For Analysis',
            'view_mode': 'list,form',
            'views': [(tree_view_id, 'list'), (form_view_id, 'form')],
            'res_model': 'project.requirement',
            'domain': [('meta_project_requirement_id', '=', self.id)],
        }
