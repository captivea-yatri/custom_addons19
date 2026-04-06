from odoo import fields, models, api, _


class ProjectDomainHistory(models.Model):
    _name = 'project.domain.history'
    _description = 'Project Domain History'
    _order = 'name'

    name = fields.Char(string='Name', compute="compute_name_based_on_default_domain_id_or_project_id",
                       readonly=True, store=True)
    default_domain_id = fields.Many2one('default.domain', string='Default Domain')
    project_id = fields.Many2one('project.project', string='Project')
    status = fields.Selection(
        [('not started', 'Not Started'), ('in progress', 'In Progress'), ('feedback', 'Feedback'), ('done', 'Done')],
        default="not started")
    phase_id = fields.Many2one('project.phase', string='Phase', domain="[('project_id', '=', project_id)]")
    project_manager_time = fields.Float(string='Req Project Manager Time')
    business_analyst_time = fields.Float(string='Req Configurator Time')
    configurator_time = fields.Float(string='Configurator Time')
    developer_time = fields.Float(string='Req Developer Time')
    architect_time = fields.Float(string="Req Architect Time")
    core_time = fields.Float(string="Req Core Time")
    implementation_time = fields.Float(string="Req Implementation Time")
    local_time = fields.Float(string="Req Local Time")
    offshore_time = fields.Float(string="Req Offshore Time")
    estimated_time = fields.Float(string="Req Estimated time")
    task_estimated_time = fields.Float(string="Task Estimated time")
    task_passed_time = fields.Float(string="Task passed time")
    date = fields.Date(string='Date')
    project_domain_id = fields.Many2one(comodel_name='project.domain', string='Project Domain')

    @api.depends('project_domain_id')
    def compute_name_based_on_default_domain_id_or_project_id(self):
        """ This method is used to set name based on domain """
        for res in self:
            res.name = res.project_domain_id.name

    def write(self, vals):
        res = super(ProjectDomainHistory, self).write(vals)
        if vals.get('status', False):
            self.project_domain_id.status = self.status
        return res
        

