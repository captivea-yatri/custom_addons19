from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PlanningRole(models.Model):
    _inherit = 'planning.role'

    is_business_analyst = fields.Boolean(string='Is Business Analyst')
    is_project_manager = fields.Boolean(string='Is Project Manager')
    is_configurator = fields.Boolean(string='Is Configurator')
    is_developer = fields.Boolean(string='Is Developer')
    is_architect = fields.Boolean(string='Is Architect')

    @api.constrains('is_business_analyst')
    def check_unique_business_analyst(self):
        """
        Ensures that only one Planning Role record can have `is_business_analyst = True`.
        If another record already has the flag enabled, a ValidationError is raised.
        """
        for rec in self:
            if rec.is_business_analyst and self.search([('id', '!=', rec.id), ('is_business_analyst', '=', True)]):
                raise ValidationError("Business Analyst is unique")

    @api.constrains('is_project_manager')
    def check_unique_project_manager(self):
        """
        Ensures that only one Planning Role record can have `is_project_manager = True`.
        Prevents multiple roles from being marked as Project Manager.
        """
        for rec in self:
            if rec.is_project_manager and self.search([('id', '!=', rec.id), ('is_project_manager', '=', True)]):
                raise ValidationError("Project Manager is unique")

    @api.constrains('is_configurator')
    def check_unique_configurator(self):
        """
        Ensures that only one Planning Role record can have `is_configurator = True`.
        Enforces unique selection for the Configurator role.
        """
        for rec in self:
            if rec.is_configurator and self.search([('id', '!=', rec.id), ('is_configurator', '=', True)]):
                raise ValidationError("Configurator is unique")

    @api.constrains('is_developer')
    def check_unique_developer(self):
        """
        Ensures that only one Planning Role record can have `is_developer = True`.
        Restricts multiple records from being tagged as Developer.
        """
        for rec in self:
            if rec.is_developer and self.search([('id', '!=', rec.id), ('is_developer', '=', True)]):
                raise ValidationError("Developer is unique")

    @api.constrains('is_architect')
    def check_unique_architect(self):
        """
        Ensures that only one Planning Role record can have `is_architect = True`.
        Guarantees the Architect role remains unique in the system.
        """
        for rec in self:
            if rec.is_architect and self.search([('id', '!=', rec.id), ('is_architect', '=', True)]):
                raise ValidationError("Architect is unique")
