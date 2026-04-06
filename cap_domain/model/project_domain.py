from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProjectDomain(models.Model):
    _name = 'project.domain'
    _description = 'Project Domain Information'

    name = fields.Char(string='Name', compute='compute_name', store=True)
    default_domain_id = fields.Many2one('default.domain', string='Default Domain')
    project_id = fields.Many2one('project.project', string='Project',
                                 domain=lambda self: [('company_id', '=', self.env.company.id)])
    status = fields.Selection(
        [('not started', 'Not Started'), ('in progress', 'In Progress'), ('feedback', 'Feedback'), ('done', 'Done')],
        default="not started")
    phase_id = fields.Many2one('project.phase', string='Phase', domain="[('project_id', '=', project_id)]")
    is_pm = fields.Boolean(string='Is Manager', compute='_compute_is_user_pm_admin')
    sequence = fields.Integer(related="default_domain_id.sequence", store=True, string='Sequence')

    def _compute_is_user_pm_admin(self):
        """
        Here, we check current user is pm of project which is set on project domain.
        If the current user is pm of project or he has group administration(access rights) then,
        he is able to edit the name of project domain.
        """
        for rec in self:
            if rec.project_id.user_id == self.env.user or self.env.user.has_group("base.group_erp_manager"):
                rec.is_pm = True
            else:
                rec.is_pm = False

    @api.depends('default_domain_id')
    def compute_name(self):
        """ This method is used to set name based on project or domain """
        for res in self:
            res.name = res.default_domain_id.name

    @api.constrains('default_domain_id', 'project_id')
    def check_unique_default_domain_and_project(self):
        """ This method is used to restrict duplication of default domain and project """
        for rec in self:
            if rec:
                res = self.search([('id', '!=', rec.id),
                                   ('default_domain_id', '=', rec.default_domain_id.id),
                                   ('project_id', '=', rec.project_id.id), ('phase_id', '=', rec.phase_id.id)])
                if res:
                    raise ValidationError(
                        "Domain: '{}' Or Phase: '{}' are already Exists for Project '{}'".format(
                            rec.phase_id.name,
                            rec.default_domain_id.name,
                            rec.project_id.name))
