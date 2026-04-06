from odoo import api, fields, models
from datetime import timedelta


class Project(models.Model):
    _inherit = 'project.project'

    milestone_ids = fields.One2many('project.milestone', 'project_id')
    signatory_progress_report_partner_id = fields.Many2one('res.partner',
                                                        string="Signatory Project Progress Report")
    signatory_portal_report_partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids')
    cc_progress_report_user_ids = fields.Many2many('res.users', 'rel_project_user_res_users', 'partner_id',
                                                   'user_id', string="CC Project Progress Report",
                                                   domain=lambda self: [('groups_id', 'in',
                                                                         [self.env.ref(
                                                                             'base.group_user').id,
                                                                          self.env.ref(
                                                                              'base.group_portal').id])])
    cc_progress_report_partner_ids = fields.Many2many('res.partner', 'res_partner_refere', 'partner_id', 'project_id',
                                                      string="CC Project Progress Report")
    cc_progress_report_internal_partner_partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids')
    project_progress_ids = fields.One2many('project.progress', 'project_id')
    next_expected_project_progress_report_date = fields.Date(string="Next Expected Project Progress Report Date",
                                                             compute='compute_next_expected_report_date',store=True)

    @api.depends('partner_id')
    def _compute_partner_ids(self):
        for rec in self:
            if rec.partner_id.parent_id:
                parent_partner = rec.partner_id.parent_id
                all_related_partners = parent_partner.child_ids | parent_partner
            else:
                all_related_partners = rec.partner_id.child_ids | rec.partner_id
            all_related_partners = all_related_partners.filtered(lambda e: e.email)
            if all_related_partners:
                rec.signatory_portal_report_partner_ids = all_related_partners
            else:
                rec.signatory_portal_report_partner_ids = False
            rec.cc_progress_report_internal_partner_partner_ids = self.env['res.users'].search(
                [('group_ids', 'in',[self.env.ref('base.group_user').id])]).mapped('partner_id') + all_related_partners

    @api.depends('project_progress_ids','project_progress_ids.status','report_frequency_in_days')
    def compute_next_expected_report_date(self):
        for rec in self:
            if not rec.project_progress_ids:
                rec.next_expected_project_progress_report_date = False
                continue
            latest_report = rec.project_progress_ids.sorted(key='create_date', reverse=True)[0]
            if latest_report.status == 'sent' and rec.report_frequency_in_days:
                rec.next_expected_project_progress_report_date = (
                        latest_report.create_date.date() + timedelta(days=rec.report_frequency_in_days)
                )

    def action_get_project_progress_report(self):
        action = self.env['ir.actions.act_window']._for_xml_id('cap_project_progress_report.project_progress_action')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

class ProjectTasks(models.Model):
    _inherit = "project.task"

    select = fields.Boolean("Select")
    sequence = fields.Integer(string='Sequence')

    def write(self, vals):
        """
        To avoid error 'One parameter is missing to use this method. You should give a start and end dates.' From base,
        When we create project progress report.
        """
        if self._context and self._context.get('from_project_progress', False):
            return super(ProjectTasks, self.with_context(fsm_mode=True)).write(vals)
        else:
            return super(ProjectTasks, self).write(vals)
