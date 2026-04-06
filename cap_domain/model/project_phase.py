from odoo import fields, models, api
from odoo.osv import expression


class ProjectPhase(models.Model):
    _name = 'project.phase'
    _description = 'Ksc Phase Information'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True)
    project_id = fields.Many2one(comodel_name="project.project", string="Project")
    active = fields.Boolean(default=True, string="Active", copy=False)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    filtered_default_domain_ids = fields.Many2many('default.domain',
                                                   compute='_compute_filtered_default_domain_ids_from_project',
                                                   string='Filtered Default Domain IDs', precompute=True)
    complementary_default_domain_ids = fields.Many2many('default.domain', 'project_phase_domain_rel', 'phase_id',
                                                        'domain_id',
                                                        string='Complementary Domains',
                                                        domain="[('active', '=',True),('all_phases', '=',True),('id','in',filtered_default_domain_ids)]",
                                                        compute='_compute_complementary_default_domain_ids',
                                                        store=True,
                                                        readonly=False,
                                                        precompute=True,
                                                        )

    @api.depends('filtered_default_domain_ids')
    def _compute_complementary_default_domain_ids(self):
        """Computes the complementary domains available for a phase.
    Filters domains based on activity, phase applicability, and those allowed by the project."""
        for rec in self:
            rec._compute_filtered_default_domain_ids_from_project()
            rec.complementary_default_domain_ids = [(6, 0, self.env['default.domain'].search(
                [('active', '=',True),('all_phases', '=', True), ('id', 'in', rec.filtered_default_domain_ids.ids)]).ids)]

    @api.depends('complementary_default_domain_ids')
    def _compute_filtered_default_domain_ids_from_project(self):
        """  Computes the filtered domain list from the associated project.
    Pulls the allowed domains from the project's configuration."""
        for rec in self:
            rec.filtered_default_domain_ids = [(6, 0, rec.project_id.filtered_default_domain_ids.ids)]

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        """
        This method is used to search phase based on project phase and get context from session test view
        """
        domain = args
        project_id = self.env['project.project'].browse(self.env.context.get('project_id'))
        if project_id:
            domain = expression.AND([
                domain,
                [('id', 'in', project_id.phase_ids.ids)]
            ])
        return super(ProjectPhase, self)._name_search(name, domain, operator, limit, order)

    @api.model
    def _search(self, domain, offset=0, limit=None, order='sequence', active_test=True,):
        """  Overrides the search method to enforce ordering by sequence.
    Delegates search logic to the parent model while keeping custom ordering."""
        return super(ProjectPhase, self)._search(domain, offset=offset, limit=limit, order='sequence', active_test=active_test,)

    @api.model
    def write(self, vals):
        """Overrides write to detect newly added complementary domains.
    When domains are added, updates project-level domain relations accordingly.
    Ensures phase-level domain additions reflect in the project domain model."""
        res = super(ProjectPhase, self).write(vals)
        for rec in self:
            newly_added_ids_of_domain_in_phase = []
            if vals.get('complementary_default_domain_ids'):
                values_in_write = vals.get('complementary_default_domain_ids')
                for object in values_in_write:
                    if object[0] == 4:
                        newly_added_ids_of_domain_in_phase.append(object[1])
            if not newly_added_ids_of_domain_in_phase == []:
                default_domains = self.env['default.domain'].search([('id', 'in', newly_added_ids_of_domain_in_phase)])
                rec.project_id.create_project_domain_based_on_phase(rec.project_id, default_domains, rec)
                rec.project_id.find_project_domain_based_on_domain(default_domains, rec)
        return res
