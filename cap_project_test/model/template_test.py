from odoo import models, fields, api


class TemplateTest(models.Model):
    _name = 'template.test'
    _description = 'Template Test Information'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    template_requirement_id = fields.Many2one(comodel_name='template.requirement', string='Template Requirement',
                                              required=True)
    template_domain_id = fields.Many2one(comodel_name='default.domain', string='Template Domain',
                                         related='template_requirement_id.template_domain_id', store=True)
    tag_ids = fields.Many2many(comodel_name='project.tags', table_name='project_tag_id', string='Tags')
    description = fields.Html(string='Description')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'default_template_requirement_id' in self.env.context:
                vals['template_requirement_id'] = self.env.context['default_template_requirement_id']
            return super(TemplateTest, self).create(vals)
