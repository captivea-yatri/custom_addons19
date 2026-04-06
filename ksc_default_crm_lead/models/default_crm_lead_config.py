from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DefaultCrmLeadConfig(models.Model):
    _name = 'default.crm.lead.config'
    _description = "Default Crm Lead Config"

    name = fields.Char(string="Name")
    website_id = fields.Many2one(string="Website", comodel_name='website', copy=False)
    country_id = fields.Many2one(string="Country", comodel_name='res.country', copy=False)
    company_id = fields.Many2one(string="Company", comodel_name='res.company')
    team_id = fields.Many2one(string='Sales Team', comodel_name='crm.team',
                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.constrains('website_id', 'country_id')
    def _unique_country_and_website_id(self):
        """
        This method is used to add restriction based on country and website
        """
        for rec in self:
            check_country_and_website = rec.search([('id', '!=', rec.id), ('website_id', '=', rec.website_id.id),
                                                    ('country_id', '=', rec.country_id.id)])
            if check_country_and_website:
                raise ValidationError("Configuration must be Unique country / website!")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            rec.team_id = ""
            rec.website_id = ""

    def copy(self, default=None):
        if not self.id:
            raise ValidationError(_("Record does not Exist"))
        return super(DefaultCrmLeadConfig, self).copy(default)

