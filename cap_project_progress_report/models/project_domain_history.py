from odoo import fields, models, api, _


class ProjectDomainHistory(models.Model):
    _inherit = 'project.domain.history'

    project_progress_id = fields.Many2one("project.progress", string="Project Progress")
    task_progress = fields.Float(
        string='Task Progress (%)',
        compute='_compute_task_progress',
        help="Average progress of all tasks related to this project domain and phase."
    )

    def _compute_task_progress(self):
        """
        Compute number of tasks and average progress based on
        project, domain, and phase.
        """
        Task = self.env['project.task']
        for record in self:
            record.task_progress = 0.0

            if not record.project_id or not record.default_domain_id or not record.phase_id:
                continue
            domain = [
                ('project_id', '=', record.project_id.id),
                ('default_domain_id', '=', record.default_domain_id.id),
                ('default_phase_id', '=', record.phase_id.id),
            ]
            tasks = Task.search(domain)
            task_count = len(tasks)
            if task_count > 0:
                total_progress = sum(tasks.mapped('progress'))
                record.task_progress = (total_progress / len(tasks)) * 100
