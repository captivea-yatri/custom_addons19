from odoo import fields, models, api


class MetaTemplateRequirement(models.Model):
    _name = 'meta.template.requirement'
    _description = 'Meta Template Requirement'

    name = fields.Char(string="Name")
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
