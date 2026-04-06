from odoo import models, fields, _, api


class ProjectDomain(models.Model):
    _inherit = 'project.domain'


    def remove_unused_domain(self):
        req_domain_ids = self.env['project.feedback'].search(
            [('project_id', 'in', self.project_id.ids), ('domain_id', 'in', self.ids)]).mapped('domain_id')
        need_to_remove_domain_ids = self - req_domain_ids
        super(ProjectDomain, need_to_remove_domain_ids).remove_unused_domain()


    def access_feedback_record(self):
        """
        This function is used to open task requirement view
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Domain',
            'view_mode': 'list,form',
            'res_model': 'project.feedback',
            'domain': [('domain_id', '=', self.id), ('default_domain_id', '=', self.default_domain_id.id),
                       ('project_id', '=', self.project_id.id),('phase_id', '=', self.phase_id.id)],
        }