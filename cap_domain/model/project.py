from odoo import fields, models, api, Command
from datetime import date, timedelta


class Project(models.Model):
    _inherit = 'project.project'

    default_domain_ids = fields.Many2many('default.domain', 'project_default_domain_rel', 'project_id', 'domain_id',
                                          string='Default Domain', tracking=True)
    project_domain_ids = fields.One2many('project.domain', 'project_id', string='Project Domain')
    phase_ids = fields.One2many('project.phase', 'project_id', string='Project', context={'active_test':False})

    # todo:need to remove this field and its compute_method in cap offer module
    filtered_default_domain_ids = fields.Many2many('default.domain', compute='_compute_filtered_default_domain_ids',
                                                   string='Filtered Default Domain IDs')

    # todo: override this method in model cap_offer and use the field condition allow_offer_date
    @api.depends('sale_order_ids')
    def _compute_filtered_default_domain_ids(self):
        """
        Filter the all domain from each sale order product default domain.
        """
        for project in self:
            # if (project.create_date and project.company_id.allow_offer_date and
            #         project.create_date.date() >= project.company_id.allow_offer_date and project.offer_id):
            #     if project.offer_id.restrict_time:
            #         order_line = project.sale_order_ids.mapped('order_line')
            #         project.filtered_default_domain_ids = [(6, 0, order_line.product_id.default_domain_ids.ids)]
            #     elif not project.offer_id.restrict_time:
            #         default_domain_ids = self.env['default.domain'].search([('offer_ids', 'in', project.offer_id.ids)])
            #         project.filtered_default_domain_ids = [(6, 0, default_domain_ids.ids)]
            # else:
            project.filtered_default_domain_ids = [(6, 0, self.env['default.domain'].search([]).ids)]


    def automatic_remove_role_project(self):
        """
        remove role if employee has not log timesheeet b/w 30 days
        """
        user_ids = self.env['res.users'].search([('share', '=', False)])
        days_after = (date.today() - timedelta(days=30))
        for user in user_ids:
            project_domain = [('create_date', '<', days_after), '|', '|',
                              ('business_analyst_ids', '=', user.id), ('developers_ids', '=', user.id),
                              ('configurators_ids', '=', user.id)]
            project_ids = self.env['project.project'].search(project_domain)
            for project in project_ids:
                timesheet_domain = [('date', '>', days_after),('project_id', '=', project.id), ('employee_id.user_id', '=', user.id)]
                timesheet_ids = self.env['account.analytic.line'].search(timesheet_domain)
                if timesheet_ids:
                    project.romove_role_project_timesheet(project, user,timesheet_ids)
                else:
                    project.business_analyst_ids = [(3, user.id)]
                    project.developers_ids = [(3, user.id)]
                    project.configurators_ids = [(3, user.id)]

    def romove_role_project_timesheet(self, project,user, timesheet_ids):
        business_rol_timesheet_ids = timesheet_ids.filtered(lambda m:  m.task_id.role_id.is_business_analyst and m.employee_id.user_id.id == user.id)
        developer_rol_timesheet_ids = timesheet_ids.filtered(lambda m: m.task_id.role_id.is_developer and m.employee_id.user_id.id == user.id)
        configuration_rol_timesheet_ids = timesheet_ids.filtered(lambda m: m.task_id.role_id.is_configurator and m.employee_id.user_id.id == user.id)
        if not business_rol_timesheet_ids:
                project.business_analyst_ids = [(3, user.id)]
        if not developer_rol_timesheet_ids:
                project.developers_ids = [(3, user.id)]
        if not configuration_rol_timesheet_ids:
                project.configurators_ids = [(3, user.id)]


    @api.model_create_multi
    def create(self, vals_list):
        """ This method is used to link or create project domain based on default domain """
        for vals in vals_list:
            if vals.get('default_domain_ids'):
                result = super(Project, self).create(vals_list)
                for rec in result:
                    rec.phase_ids = [
                        (0, 0, {'name': 'Phase 1', 'project_id': rec.id})] if not rec.phase_ids else rec.phase_ids
                    rec.create_project_domain_based_on_phase(rec, rec.default_domain_ids, rec.phase_ids)
                return result
            else:
                return super(Project, self).create(vals_list)

    def write(self, vals):
        """ This method is used to link or create project domain based on default domain """
        domain_ids = self.default_domain_ids
        phase_ids = self.phase_ids
        if vals.get('default_domain_ids') or vals.get('phase_ids'):
            result = super(Project, self).write(vals)
            domain_ids = self.default_domain_ids - domain_ids
            phase_ids = self.phase_ids - phase_ids
            for rec in self:
                extra_domain_from_phase = self.env['default.domain']
                if domain_ids and not rec.phase_ids:
                    rec.phase_ids = [(0, 0, {'name': 'Phase 1', 'project_id': rec.id})]
                    for phase in rec.phase_ids.filtered(lambda phs: phs.complementary_default_domain_ids):
                        extra_domain_from_phase += phase.complementary_default_domain_ids
                    rec.create_project_domain_based_on_phase(rec, domain_ids + extra_domain_from_phase, rec.phase_ids)
                elif domain_ids and not phase_ids:
                    rec.create_project_domain_based_on_phase(rec, domain_ids, rec.phase_ids)
                elif phase_ids and not domain_ids:
                    for phase in phase_ids.filtered(lambda phs: phs.complementary_default_domain_ids):
                        extra_domain_from_phase = phase.complementary_default_domain_ids
                        rec.create_project_domain_based_on_phase(rec, rec.default_domain_ids + extra_domain_from_phase,
                                                                 phase)
                elif phase_ids and domain_ids:
                    for phase in phase_ids.filtered(lambda phs: phs.complementary_default_domain_ids):
                        extra_domain_from_phase += phase.complementary_default_domain_ids
                    rec.create_project_domain_based_on_phase(rec, domain_ids , rec.phase_ids)
                    rec.create_project_domain_based_on_phase(rec, rec.default_domain_ids + extra_domain_from_phase, phase_ids)
            return result
        else:
            return super(Project, self).write(vals)

    def create_project_domain_based_on_phase(self, rec, default_domain_ids, phase_ids):
        """ This method is used to link or create project domain based on default domain """
        for default_domain_id in default_domain_ids:
            if default_domain_id.all_phases:
                for phase_id in phase_ids:
                    rec.search_and_create_project_domain_based_on_phase(rec, default_domain_id, phase_id)
            elif rec.phase_ids:
                rec.search_and_create_project_domain_based_on_phase(rec, default_domain_id, rec.phase_ids[0])

    def search_and_create_project_domain_based_on_phase(self, rec, default_domain_id, phase_id):
        """
         This method is used to create project domain based on phase
        """
        project_domain_id = rec.project_domain_ids.search([('default_domain_id', '=', default_domain_id.id),
                                                           ('project_id', '=', rec.id),
                                                           ('phase_id', '=', phase_id.id)])
        if not project_domain_id:
            project_domain = rec.project_domain_ids.create({'default_domain_id': default_domain_id.id,
                                                            'project_id': rec.id,
                                                            'phase_id': phase_id.id
                                                            })
            rec.project_domain_ids = [(4, project_domain.id)]

    def action_project_domain(self):
        """
         This function is used to open project Domain Views
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Domains',
            'view_mode': 'pivot,tree,form',
            'views': [(self.env.ref('cap_domain.project_domain_pivot_view').id, 'pivot'),
                      (self.env.ref('cap_domain.project_domain_tree_view_for_project_view').id, 'list'),
                      (self.env.ref('cap_domain.project_domain_form_view').id, 'form')],
            'res_model': 'project.domain',
            'context': {'default_project_id': self.id, 'create': False, 'delete': False}, #,'search_default_phase_id': 1
            'domain': [('project_id', '=', self.id)],
        }

    def _mail_track(self, tracked_fields, initial_values):
        changes, tracking_value_ids = super()._mail_track(tracked_fields, initial_values)
        # Many2many tracking
        if len(changes) > len(tracking_value_ids):
            for changed_field in changes:
                if tracked_fields[changed_field]['type'] in ['one2many', 'many2many']:
                    field = self.env['ir.model.fields']._get(self._name, changed_field)
                    vals = {
                        'field': field.id,
                        'field_desc': field.field_description,
                        'field_type': field.ttype,
                        'tracking_sequence': field.tracking,
                        'old_value_char': ', '.join(initial_values[changed_field].mapped('name')),
                        'new_value_char': ', '.join(self[changed_field].mapped('name')),
                    }
                    tracking_value_ids.append(Command.create(vals))
        return changes, tracking_value_ids
