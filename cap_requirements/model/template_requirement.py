from odoo import fields, models, api


class TemplateRequirement(models.Model):
    _name = 'template.requirement'
    _description = 'Template Requirement Information'

    template_domain_id = fields.Many2one(comodel_name='default.domain', string='Template Domain')
    tag_ids = fields.Many2many('project.tags',column1='template_requirment_id', column2='project_tags_id',
                               string='Tags')
    name = fields.Char(string='Name', translate=True)
    description = fields.Html(string='Description', translate=True)
    role_id = fields.Many2one(comodel_name='planning.role', string='Role')
    default_estimate_time = fields.Float(string='Default Estimate Time')
    deliverable_from_the_customer = fields.Text(string='Deliverable From The Customer', translate=True)
    questions_to_ask = fields.Text(string='Questions To Ask', translate=True)
    help = fields.Html(string='Help', translate=True)
    meta_template_requirement_id = fields.Many2one(comodel_name='meta.template.requirement',
                                                   string='Meta Template Requirement')
    all_apps = fields.Boolean(default=False, string="For all Apps and All Phase ?", copy=False)
    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(default=True)
    is_answer_mandatory = fields.Boolean(string='Answer mandatory')

    @api.onchange('all_apps')
    def onchange_all_apps(self):
        """
        This method is used to remove template domain if all_apps is true
        """
        if self.all_apps:
            self.template_domain_id = False
