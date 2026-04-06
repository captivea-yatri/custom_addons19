from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval


class Project(models.Model):
    _inherit = 'project.project'

    def action_project_workshop(self):
        """
            This function is used to open project requirement Views
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Requirement',
            'view_mode': 'list,form,pivot',
            'res_model': 'project.requirement',
            'context': {'search_default_default_domain_id': 1,
                        'default_project_id': self.id},
            'domain': [('project_id', '=', self.id),
                       '|', ('template_requirements_id', '=', False), ('template_requirements_id.all_apps', '=', False)]
        }

    def action_project_analysis(self):
        """
            This function is used to open project requirement Views
        """
        tree_view_id = self.env.ref('cap_requirements.project_requirement_tree_view_for_analysis').id
        form_view_id = self.env.ref('cap_requirements.project_requirement_form_view').id
        pivot_view_id = self.env.ref('cap_requirements.project_requirement_pivot_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Requirement For Analysis',
            'view_mode': 'list,form,pivot',
            'views': [(tree_view_id, 'list'), (form_view_id, 'form'), (pivot_view_id, 'pivot')],
            'res_model': 'project.requirement',
            'context': {
                'search_default_phase_id': self.phase_ids.ids if self.phase_ids else False,
                'search_default_default_domain_id': self.default_domain_ids if self.default_domain_ids else False,
                'default_project_id': self.id},
            'domain': [('project_id', '=', self.id)],
        }

    def find_project_requirement(self, template_requirement_id=False, phase_id=False, default_domain_id=False,
                                 project_domain_id=False):
        """
        This method is used to find the project requirement based on project, domain and phase
        """
        domain = [('project_id', '=', self.id), '|', ('project_domain_id', 'in', self.project_domain_ids.ids),
                  ('default_domain_id', 'in', self.default_domain_ids.ids)]
        if project_domain_id and default_domain_id:
            domain = [('project_id', '=', self.id), '|', ('project_domain_id', '=', project_domain_id.id),
                      ('default_domain_id', '=', default_domain_id.id)]
        if template_requirement_id:
            domain += [('template_requirements_id', '=', template_requirement_id.id)]
        if phase_id:
            domain += [('phase_id', '=', phase_id)]
        else:
            domain += [('phase_id', 'in', self.phase_ids.ids)]
        return self.env['project.requirement'].search(domain)

    @api.model_create_multi
    def create(self, vals_list):
        """ This method is used to link or create project requirement based on default domain or phase"""
        for vals in vals_list:
            if vals.get('default_domain_ids') or vals.get('phase_ids'):
                result = super(Project, self).create(vals)
                for rec in result:
                    rec.create_project_requirement_based_on_phase_or_domain(rec.project_domain_ids, rec.phase_ids)
                return result
            else:
                return super(Project, self).create(vals)

    def create_project_requirement_based_on_phase_or_domain(self, project_dommain_ids, phase_ids):
        """
            This method is used to create project requirement based on template requirement
        """
        for project_domain_id in project_dommain_ids:
            # check the template requirement which is based on domain and which has not all_apps
            template_requirement_ids = self.env['template.requirement'].search(
                [('template_domain_id', '=', project_domain_id.default_domain_id.id), ('all_apps', '=', False),('active','=',True)])
            for template_requirement_id in template_requirement_ids:
                if project_domain_id.default_domain_id.all_phases:
                    for phase_id in phase_ids:
                        project_requirement_ids = self.find_project_requirement(
                            template_requirement_id=template_requirement_id,
                            phase_id=phase_id.id,
                            default_domain_id=project_domain_id.default_domain_id,
                            project_domain_id=project_domain_id)
                        if not project_requirement_ids:
                            self.create_project_requirement(template_requirement_id, project_domain_id,
                                                            phase_id)
                else:
                    project_requirement_ids = self.find_project_requirement(
                        template_requirement_id=template_requirement_id,
                        phase_id=False,
                        default_domain_id=project_domain_id.default_domain_id,
                        project_domain_id=project_domain_id)
                    if not project_requirement_ids:
                        self.create_project_requirement(template_requirement_id, project_domain_id)
            # check the template requirement which is based on all_apps
            template_requirement_ids = self.env['template.requirement'].search([('all_apps', '=', True)])
            for template_requirement_id in template_requirement_ids:
                if project_domain_id.default_domain_id.is_an_app:
                    if project_domain_id.default_domain_id.all_phases:
                        for phase_id in phase_ids:
                            project_requirement_ids = self.find_project_requirement(
                                template_requirement_id=template_requirement_id,
                                phase_id=phase_id.id, default_domain_id=project_domain_id.default_domain_id,
                                project_domain_id=project_domain_id)
                            if not project_requirement_ids:
                                self.create_project_requirement(template_requirement_id,
                                                                project_domain_id,
                                                                phase_id)
                    else:
                        project_requirement_ids = self.find_project_requirement(
                            template_requirement_id=template_requirement_id, phase_id=False,
                            default_domain_id=project_domain_id.default_domain_id,
                            project_domain_id=project_domain_id)
                        if not project_requirement_ids:
                            self.create_project_requirement(template_requirement_id, project_domain_id)

    def find_project_domain_based_on_domain(self, domain_ids, phase_ids):
        project_domain_ids = self.project_domain_ids.search(
            [('project_id', '=', self.id), ('default_domain_id', 'in', domain_ids.ids),
             ('phase_id', 'in', phase_ids.ids)])
        self.create_project_requirement_based_on_phase_or_domain(project_domain_ids, phase_ids)

    def write(self, vals):
        """
        This method is used to create project requirement based on template requirement
        """
        domain_ids = self.default_domain_ids
        phase_ids = self.phase_ids
        if vals.get('default_domain_ids') or vals.get('phase_ids'):
            result = super(Project, self).write(vals)
            domain_ids = self.default_domain_ids - domain_ids
            phase_ids = self.phase_ids - phase_ids
            for rec in self:
                if domain_ids and not phase_ids:
                    rec.find_project_domain_based_on_domain(domain_ids, rec.phase_ids)
                elif not domain_ids and phase_ids:
                    for phase in phase_ids.filtered(lambda phs: phs.complementary_default_domain_ids):
                        extra_domain_from_phase = phase.complementary_default_domain_ids
                        rec.find_project_domain_based_on_domain(rec.default_domain_ids + extra_domain_from_phase, phase)
                elif phase_ids and domain_ids:
                    extra_domain_from_phase = self.env['default.domain']
                    for phase in rec.phase_ids.filtered(lambda phs: phs.complementary_default_domain_ids):
                        extra_domain_from_phase += phase.complementary_default_domain_ids
                    rec.find_project_domain_based_on_domain(rec.default_domain_ids + extra_domain_from_phase, phase_ids)
                    rec.find_project_domain_based_on_domain(domain_ids, rec.phase_ids)
            return result
        else:
            return super(Project, self).write(vals)

    def create_project_requirement(self, template_requirement_id, project_domain_id, phase_id=False):
        """
        This method is used to create project requirement data
        """
        phase_id = phase_id if phase_id else project_domain_id.phase_id
        vals = {
            'template_requirements_id': template_requirement_id.id,
            'project_id': self.id,
            'phase_id': phase_id.id,
            'description': template_requirement_id.description,
            'name': template_requirement_id.name,
            'role_id': template_requirement_id.role_id.id,
            'tag_ids': [(6, 0, template_requirement_id.tag_ids.ids)],
            # 'estimate_time': template_requirement_id.default_estimate_time,
            'deliverable_from_the_customer': template_requirement_id.deliverable_from_the_customer,
            'questions_to_ask': template_requirement_id.questions_to_ask,
            'project_domain_id': project_domain_id.id,
            'default_domain_id': project_domain_id.default_domain_id.id
        }
        if template_requirement_id.meta_template_requirement_id:
            meta_project_requirement = self.env['meta.project.requirement'].search([('project_id', '=', self.id), (
                'meta_template_requirement_id', '=', template_requirement_id.meta_template_requirement_id.id)])
            if meta_project_requirement:
                vals.update({'meta_project_requirement_id': meta_project_requirement.id})
            else:
                meta_project_requirement_id = self.env['meta.project.requirement'].create(
                    {'name': template_requirement_id.meta_template_requirement_id.name,
                     'project_id': self.id,
                     'meta_template_requirement_id': template_requirement_id.meta_template_requirement_id.id,
                     'calculation_formula': template_requirement_id.meta_template_requirement_id.calculation_formula,
                     })
                vals.update({'meta_project_requirement_id': meta_project_requirement_id.id})
        self.env['project.requirement'].create(vals)

    def remove_unused_project_domain(self, project_requirement_ids, req_project_domain_ids=[]):
        """
        This method is used to remove project domain which have not any project requirement
        """
        req_project_domain_ids += project_requirement_ids.project_domain_id.ids
        project_domain_ids = self.project_domain_ids.search(
            [('id', 'not in', req_project_domain_ids), ('project_id', '=', self.id)])
        if project_domain_ids:
            task_ids = self.env['project.task'].search(
                [('project_id', '=', self.id), ('default_phase_id', 'in', project_domain_ids.phase_id.ids),
                 ('project_domain_id', 'in', project_domain_ids.ids),
                 ('default_domain_id', 'in', project_domain_ids.default_domain_id.ids)])
            if not task_ids:
                project_domain_ids.unlink()
            else:
                project_domain_ids -= task_ids.project_domain_id
                project_domain_ids.unlink()

    def action_calculate_estimate_time(self):
        """
        This method is used to calculate the advised estimate time based on meta project requirement's python code
        """
        project_requirement_ids = self.find_project_requirement(template_requirement_id=False)
        self.remove_unused_project_domain(project_requirement_ids)
        for project_requirement_id in project_requirement_ids:
            template_req_id = project_requirement_id.template_requirements_id
            if template_req_id:
                project_domain_id = project_requirement_id.project_domain_id
                meta_project_requirement_id = project_requirement_id.meta_project_requirement_id
                if project_domain_id and meta_project_requirement_id:
                    localdict = {
                        'PM_TIME': project_domain_id.project_manager_time,
                        'BA_TIME': project_domain_id.business_analyst_time,
                        'CONF_TIME': project_domain_id.configurator_time,
                        'DEV_TIME': project_domain_id.developer_time,
                        'ARCH_TIME': project_domain_id.architect_time
                    }
                    try:
                        safe_eval(
                            project_requirement_id.meta_project_requirement_id.calculation_formula or 0.0,
                            localdict, mode='exec', nocopy=True)
                        if project_requirement_id.manual_estimate:
                            self.env.cr.execute("""UPDATE project_requirement
                                                   SET advised_estimated_time = %s
                                                   WHERE id = %s
                                                """, (localdict['result'], project_requirement_id.id))
                        else:
                            self.env.cr.execute("""
                                            UPDATE project_requirement
                                            SET advised_estimated_time = %s, estimate_time = %s
                                            WHERE id = %s
                                        """, (localdict['result'], localdict['result'], project_requirement_id.id))
                    except Exception as e:
                        project_requirement_id._raise_error(
                            localdict, _("Wrong python code defined for meta template : " + str(meta_project_requirement_id.name) + " : "), e)
                elif template_req_id.default_estimate_time:
                    project_requirement_id.advised_estimated_time = template_req_id.default_estimate_time
        self.env.cr.commit()

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """
        Custom name_search for projects based on project domain and session context.
        """
        domain = domain or []
        project_id = self.browse(self.env.context.get('project_id'))
        if project_id:
            recs = self.search([('phase_ids', 'in', project_id.default_domain_ids.ids)] + domain, limit=limit)
        else:
            return super(Project, self).name_search(
                name=name,
                domain=domain,
                operator=operator,
                limit=limit
            )
        return recs.name_get()

    def refresh_project_domain_calculations(self):
        """
        call calculate_project_domain() from project.domain models
        """
        self.project_domain_ids.calculate_project_domain()
        project_requirement_ids = self.find_project_requirement(template_requirement_id=False)
        self.remove_unused_project_domain(project_requirement_ids)

