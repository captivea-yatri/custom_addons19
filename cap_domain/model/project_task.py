from odoo import fields, models, api
from odoo.exceptions import ValidationError


PROJECT_TASK_READABLE_FIELDS = {
    'default_domain_id',
    'default_phase_id'
}

PROJECT_TASK_WRITABLE_FIELDS = {
    'default_domain_id',
    'default_phase_id'
}


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_domain_id = fields.Many2one(comodel_name='project.domain', string='Project Domain',
                                        domain="[('project_id', '=', project_id)]")
    default_phase_id = fields.Many2one(comodel_name='project.phase', string='Phase', domain="[('project_id', '=', project_id)]", tracking=True)
    role_id = fields.Many2one(comodel_name='planning.role', string='Role')
    default_domain_ids = fields.Many2many('default.domain', 'project_default_domain_rel_related', 'project_id',
                                          'domain_id', string='Default Domain', related="project_id.default_domain_ids")
    default_domain_id = fields.Many2one(comodel_name='default.domain', string='Domain',
                                        domain="[('id', 'in', default_domain_ids)]", tracking=True)

    @property
    def SELF_READABLE_FIELDS(self):
        """
        This method is used to add read access of group by domain and phase field to portal user
        """
        return super().SELF_READABLE_FIELDS | PROJECT_TASK_READABLE_FIELDS

    @property
    def SELF_WRITABLE_FIELDS(self):
        """
        This method is used to add write access of group by domain and phase field to portal user
        """
        return super().SELF_WRITABLE_FIELDS | PROJECT_TASK_WRITABLE_FIELDS

    def write(self, vals):
        """
        Validates updates to domain or phase fields, preventing modifications
        when multiple tasks belong to different projects. Ensures domain and
        phase changes remain consistent within a single project context.
        """
        for rec in self:
            if (('default_domain_id' in vals and vals.get('default_domain_id') != rec.default_domain_id.id) or
                    ('default_phase_id' in vals and vals.get('default_phase_id') != rec.default_phase_id.id)):
                if len(self.mapped('project_id')) > 1:
                    raise ValidationError("You can not change phase or domain for multiple projects")
        return super(ProjectTask, self).write(vals)

    def _calculate_planned_dates(self, date_start, date_stop, user_id=None, calendar=None):
        """
        Overrides planned date calculation to allow portal users to compute
        planning values with sudo access. Other users follow the normal
        permission flow while preserving the core scheduling logic.
        """
        if self.env.user.has_group('base.group_portal'):
            return super(ProjectTask, self.sudo())._calculate_planned_dates(date_start, date_stop, user_id=None, calendar=None)
        else:
            return super(ProjectTask, self)._calculate_planned_dates(date_start, date_stop, user_id=None,
                                                                            calendar=None)
    @api.onchange('stage_id')
    def update_project_domain_status(self):
        """
        Updates the domain status when the task stage changes. If the task enters
        the required stage and the related project domain is still 'not started',
        its status is automatically moved to 'in progress'.
        """
        # TODO : need to check in database
        if self.stage_id.id == 11 and self.project_domain_id.status == 'not started' and self.default_phase_id.id == self.project_domain_id.phase_id.id:
            self.project_domain_id.status = 'in progress'




