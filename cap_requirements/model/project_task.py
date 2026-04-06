from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_requirement_id = fields.Many2one(comodel_name='project.requirement', string='project Requirement',
                                             domain="[('project_id', '=', project_id), "
                                                    "('phase_id', '=', default_phase_id), "
                                                    "('default_domain_id', '=', default_domain_id)]")
    help = fields.Html(string='Help', compute='_compute_project_requirement', readonly=True, store=True)
    is_functional_task = fields.Boolean(string='Functional task', compute="_compute_is_functional", store=True)

    @api.depends('project_requirement_id', 'project_requirement_id.template_requirements_id.template_domain_id', 'project_requirement_id.template_requirements_id.meta_template_requirement_id')
    def _compute_is_functional(self):
        for rec in self:
            if not rec.project_requirement_id:
                rec.is_functional_task = True
            elif rec.project_requirement_id and rec.project_requirement_id.template_requirements_id and not rec.project_requirement_id.template_requirements_id.template_domain_id:
                rec.is_functional_task = False
            elif rec.project_requirement_id and rec.project_requirement_id.template_requirements_id and rec.project_requirement_id.template_requirements_id.meta_template_requirement_id:
                rec.is_functional_task = False
            else:
                rec.is_functional_task = True

    @api.depends('role_id', 'project_requirement_id', 'project_requirement_id.template_requirements_id.help')
    def _compute_project_requirement(self):
        """
        This Function is used to set the value of help field
        """
        for rec in self:
            if rec.role_id.is_developer or not rec.project_requirement_id:
                rec.help = """
                <h1>User Requirements</h1>
                <p>Describe here what the user wants to do and should be able to do once it is developed</p>
                <h1>Functional Requirements</h1>
                <p>Describe here what we will need to do:</p>
                <p>* Views Organization</p>
                <p>* List Of Fields (mandatory, readonly...)</p>
                """
            else:
                rec.help = rec.project_requirement_id.template_requirements_id.help

    @api.constrains('default_domain_id', 'default_phase_id', 'active')
    def create_project_domain_based_on_task_domain_and_phase(self):
        for rec in self:
            if rec.default_domain_id and rec.default_phase_id and rec.active:
                project_domain_id = rec.env['project.domain'].search(
                    [('default_domain_id', '=', rec.default_domain_id.id),
                     ('project_id', '=', rec.project_id.id),
                     ('phase_id', '=', rec.default_phase_id.id)], limit=1)
                if not project_domain_id:
                    project_domain_id = rec.env['project.domain'].create({
                        'default_domain_id': rec.default_domain_id.id,
                        'project_id': rec.project_id.id,
                        'phase_id': rec.default_phase_id.id,
                    })
                if rec.project_domain_id and rec.project_domain_id.id != project_domain_id.id:
                    old_project_domain_id = rec.project_domain_id
                    rec.project_domain_id = project_domain_id
                    old_project_domain_id.remove_unused_domain()
                rec.project_domain_id = project_domain_id
            elif not rec.active and rec.project_domain_id:
                project_domain_id = rec.project_domain_id
                rec.project_domain_id = False
                project_domain_id.remove_unused_domain()
            if rec.stage_id.id == 11 and rec.project_domain_id.status == 'not started' and rec.default_phase_id.id == rec.project_domain_id.phase_id.id:
                rec.project_domain_id.status = 'in progress'

    def unlink(self):
        """
        Unlink is inherited because when we delete task and if there is no more task of the same project domain and
        if there is no more project requirement of the same project domain. project domain must be deleted.
        """
        project_domain_ids = self.mapped('project_domain_id')
        res = super(ProjectTask, self).unlink()
        project_domain_ids.remove_unused_domain()
        return res