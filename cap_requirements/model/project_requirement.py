from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlwt
from io import BytesIO
import re


class ProjectRequirement(models.Model):
    _name = 'project.requirement'
    _description = 'Project Requirement Information'

    template_requirements_id = fields.Many2one(comodel_name='template.requirement', string='Template requirement')
    tag_ids = fields.Many2many('project.tags', column1='project_requirment_id', column2='project_tags_id',
                               string='Tags')
    project_id = fields.Many2one(comodel_name='project.project', string='Project')
    phase_id = fields.Many2one(comodel_name='project.phase', string='Phase', domain="[('project_id', '=', project_id)]",
                               required=True ,
                               help="Try to think of a way to phase your project:\n"
                                       "• Our aim is to build a MVP for phase 1\n"
                                       "• Our message is to go live as fast as possible,build your phases with that in mind.\n"
                                       "• We should always push the customer to reduce the first phase to its minimum"
                               )
    maturity = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Maturity',
                                help="Do you have all informations to do the task ?.\n"
                                "• For form modifications : should be always 'no' : We don't ask for the type of fields, name, descriptions, automations....it is not the purpose of the analysis, we have an additional analysis to do that.\n"
                                "• It can be a yes when it a simple check box to tick, you are sure of what to do.\n"
                                "• Maturity is a tool to help the discussion in the presentation : The more No you have the more uncertain is the figure given.")
    project_domain_id = fields.Many2one(comodel_name='project.domain', string='Project Domain',
                                        domain="[('project_id', '=', project_id)]")
    used = fields.Selection([('yes', 'Yes'), ('no', 'No')], help='Is the task necessary for the customer "No" has as many weight than a "yes".No means that you put aside a feature on purpose.'
                            'The customer need to see it so he can validate that we will not do it.(never remove a line)')
    name = fields.Char(string='Name', translate=True, required=True)
    description = fields.Html(string='Description', translate=True)
    role_id = fields.Many2one(comodel_name='planning.role', string='Role', required=True, help = ' Who will do the task, only one role per requirement, you can only have one responsible. Roles are also used to compute all the figures' )
    advised_estimated_time = fields.Float(string="Advised Estimated Time")
    manual_estimate = fields.Boolean(string="Manual Estimate",help = 'No 0 time ! Odoo calculate a default one, please review it'
                                 'and tick the manual box if you want to modify the advised time')
    estimate_time = fields.Float(string='Estimate Time', compute='compute_estimate_time', store=True, readonly=False, help = 'No 0 time ! Odoo calculate a default one, please review it'
                                 'and tick the manual box if you want to modify the advised time')
    module_cost = fields.Float(string='Module Cost', help='If you plan to use a module, please put the max price (if many modules available) so the customer know what to add in the project price.')
    deliverable_from_the_customer = fields.Html(string='Deliverable From The Customer', translate=True)
    questions_to_ask = fields.Html(string='Questions To Ask', translate=True)
    features_not_discussed_in_pre_sales = fields.Selection([('yes', 'Yes'), ('no', 'No')],string='Features Not Discussed In Pre Sales',
                                                           help = 'This is a field to be used when preparing the presentation with the sales :'
                                                           'often customers ask for things not expressed in presales. In such cases,it is important to be able to find out them'
                                                           ' so the sales can justify the difference between the first estimate and the analysis estimate')
    default_domain_id = fields.Many2one('default.domain', string='Default Domain')
    meta_project_requirement_id = fields.Many2one('meta.project.requirement', string="Meta Project Requirement")
    sequence = fields.Integer(string='Sequence')
    default_domain_ids = fields.Many2many('default.domain', 'project_default_domain_rel_related', 'project_id',
                                          'domain_id', string='Default Domain', related="project_id.default_domain_ids")


    def _raise_error(self, localdict, error_type, e):
        """
        This method is used to raise error if result is not get properly in python code of meta template
        """
        raise UserError(_("""%s:
    - PM_TIME: %d
    - BA_TIME: %d
    - CONF_TIME: %d
    - DEV_TIME: %d
    - ARCH_TIME: %d
    - Error: %s""") % (
            error_type,
            localdict['PM_TIME'],
            localdict['BA_TIME'],
            localdict['CONF_TIME'],
            localdict['DEV_TIME'],
            localdict['ARCH_TIME'],
            e))

    @api.constrains('default_domain_id', 'phase_id', 'project_id')
    def _check_unique_project_requirement(self):
        for rec in self:
            project_requirement = rec.search(
                [('id', '!=', rec.id), ('project_id', '=', rec.project_id.id), ('phase_id', '=', rec.phase_id.id),
                 ('default_domain_id', '=', rec.default_domain_id.id),
                 ('template_requirements_id', '=', rec.template_requirements_id.id),
                 ('template_requirements_id', '!=', False)])
            if project_requirement:
                raise ValidationError("""project requirement: '{}' is already exist with
                                      \n Project : '{}' \n Domain : '{}' And \n Phase : '{}'.""".format(
                    rec.name, rec.project_id.name, rec.default_domain_id.name, rec.phase_id.name))

    def find_project_domain(self, domain_id, project_id, phase_id):
        """
        This method is used to search project domain
        """
        project_domain_id = self.env['project.domain'].search(
            [('default_domain_id', '=', domain_id), ('project_id', '=', project_id),
             ('phase_id', '=', phase_id)], limit=1)
        return project_domain_id

    def create_project_domain(self, domain_id, project_id, phase_id):
        """
        This method is used to create project domain
        """
        project_domain_id = self.find_project_domain(domain_id, project_id, phase_id)
        if not project_domain_id:
            project_domain_id = project_domain_id.create({
                'default_domain_id': domain_id,
                'project_id': project_id,
                'phase_id': phase_id,
            })
        return project_domain_id

    def create_another_project_requirement(self, phase_id, default_domain_id):
        template_requirement_ids = self.env['template.requirement'].search(
            [('all_apps', '=', True)])
        project_requirement_id = self.search(
            [('id', '!=', self.id), ('template_requirements_id', 'in', template_requirement_ids.ids),
             ('project_id', '=', self.project_id.id),
             ('default_domain_id', '=', default_domain_id.id),
             ('phase_id', '=', phase_id)])
        if not project_requirement_id:
            for template_requirement_id in template_requirement_ids:
                if default_domain_id.is_an_app:
                    project_domain_id = self.create_project_domain(default_domain_id.id, self.project_id.id,
                                                                   phase_id)
                    vals = {
                        'template_requirements_id': template_requirement_id.id,
                        'project_id': self.project_id.id,
                        'phase_id': phase_id,
                        'description': template_requirement_id.description,
                        'name': template_requirement_id.name,
                        'role_id': template_requirement_id.role_id.id,
                        'tag_ids': [(6, 0, template_requirement_id.tag_ids.ids)],
                        'deliverable_from_the_customer': template_requirement_id.deliverable_from_the_customer,
                        'questions_to_ask': template_requirement_id.questions_to_ask,
                        'project_domain_id': project_domain_id.id,
                        'default_domain_id': default_domain_id.id
                    }
                    if template_requirement_id.meta_template_requirement_id:
                        meta_project_requirement = self.env['meta.project.requirement'].search(
                            [('project_id', '=', self.project_id.id), (
                                'meta_template_requirement_id', '=',
                                template_requirement_id.meta_template_requirement_id.id)])
                        if meta_project_requirement:
                            vals.update({'meta_project_requirement_id': meta_project_requirement.id})
                        else:
                            meta_project_requirement_id = self.env['meta.project.requirement'].create(
                                {'name': template_requirement_id.meta_template_requirement_id.name,
                                 'project_id': self.project_id.id,
                                 'meta_template_requirement_id': template_requirement_id.meta_template_requirement_id.id,
                                 'calculation_formula': template_requirement_id.meta_template_requirement_id.calculation_formula,
                                 })
                            vals.update({'meta_project_requirement_id': meta_project_requirement_id.id})
                    self.create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """
        This method is used to create project domain based on requirement
        """
        for vals in vals_list:
            project_domain_id = self.create_project_domain(vals.get('default_domain_id'), vals.get('project_id'),
                                                           vals.get('phase_id'))
            vals.update({
                'project_domain_id': project_domain_id.id
            })
            records = super(ProjectRequirement, self).create(vals)
            if not records.template_requirements_id.all_apps:
                for rec in records:
                    rec.create_another_project_requirement(rec.phase_id.id, rec.default_domain_id)
            return records

    def write(self, vals):
        """
        This method is used to create project domain as well as requirement based on requirement or phase
        """
        for rec in self:
            if (vals.get('default_domain_id') and vals.get('default_domain_id') != rec.default_domain_id.id or
                    vals.get('phase_id') and vals.get('phase_id') != rec.phase_id.id):
                if len(self.mapped('default_domain_id')) > 1:
                    raise ValidationError("You can not move project requirement with more than one domain")
                domain_id = vals.get('default_domain_id') or rec.default_domain_id.id
                phase_id = vals.get('phase_id') or rec.phase_id.id
                project_domain_id = rec.create_project_domain(domain_id, rec.project_id.id, phase_id)
                phase = rec.phase_id.browse(phase_id)
                if rec.template_requirements_id.all_apps:
                    raise UserError(
                        "You can not move project requirement : '{}' of template requirement : '{}' with all apps from phase : '{}' to phase : '{}'".format(
                            rec.name, rec.template_requirements_id.name, rec.phase_id.name, phase.name))
                if not rec.template_requirements_id.all_apps:
                    default_domain_id = self.env['default.domain'].browse(domain_id)
                    rec.create_another_project_requirement(phase_id, default_domain_id)
                    # This code is used to remove unused project requirement which has not template domain on template requirement
                    remove_project_requirement_id = self.search(
                        [('id', 'not in', self.ids),
                         ('project_id', 'in', rec.project_id.ids),
                         ('default_domain_id', '=', rec.default_domain_id.id),
                         ('phase_id', 'in', rec.phase_id.ids)])
                    rec.remove_unrequired_project_requirement(remove_project_requirement_id)
                vals.update({'project_domain_id': project_domain_id.id})
        res = super(ProjectRequirement, self).write(vals)
        for rec in self:
            project_domain_ids = self.env['project.domain'].search([('project_id', '=', rec.project_id.id)])
            project_domain_ids.remove_unused_domain()
        return res

    def remove_unrequired_project_requirement(self, remove_project_requirement_id):
        """
        This method is used to remove the unused project requirement which has not all apps and all phase
        """
        requirement_id = self.search(
            [('id', 'in', remove_project_requirement_id.ids), ('template_requirements_id', '=', False)])
        if remove_project_requirement_id and not requirement_id:
            if not remove_project_requirement_id.template_requirements_id.template_domain_id:
                remove_project_requirement_id.unlink()

    def unlink(self):
        """
        This method is used to unlink project requirement which has not linked with template domain when delete the requirement
        """
        project_domain_ids = self.mapped('project_domain_id')
        for rec in self:
            remove_project_requirement_id = self.search(
                [('id', 'not in', self.ids),
                 ('project_id', '=', rec.project_id.id),
                 ('default_domain_id', '=', rec.default_domain_id.id),
                 ('phase_id', '=', rec.phase_id.id)])
            rec.remove_unrequired_project_requirement(remove_project_requirement_id)
        # Need 2 for loops because we want to delete all the meta project requirement while delete the project requirement
        for rec in self:
            meta_project_requirement_id = self.env['meta.project.requirement'].search(
                [('id', '=', rec.meta_project_requirement_id.id)])
            if meta_project_requirement_id:
                project_requirement_ids = self.search([('id', '!=', rec.id), ('project_id', '=', rec.project_id.id), (
                    'meta_project_requirement_id', '=', meta_project_requirement_id.id)])
                if not project_requirement_ids or all(req in self for req in project_requirement_ids):
                    meta_project_requirement_id.unlink()
        res = super(ProjectRequirement, self).unlink()
        project_domain_ids.remove_unused_domain()
        return res

    @api.depends('manual_estimate', 'advised_estimated_time', 'template_requirements_id.meta_template_requirement_id')
    def compute_estimate_time(self):
        """
        This method is used to calculate estimate time based on advised estimate time or manual estimate time
        """
        for rec in self:
            if rec.manual_estimate == False and rec.template_requirements_id.meta_template_requirement_id:
                rec.estimate_time = rec.advised_estimated_time
            elif not rec.template_requirements_id.meta_template_requirement_id and rec.manual_estimate == False:
                rec.estimate_time = rec.template_requirements_id.default_estimate_time
            else:
                rec.estimate_time = rec.estimate_time

    def open_form_of_requirement(self):
        """
        This method is used to open requirement form view from tree view button
        """
        return {
            "name": _("Project Requirement"),
            'type': 'ir.actions.act_window',
            "res_model": "project.requirement",
            "res_id": self.id,
            'context': {'default_project_id': self.project_id.id},
            'views': [[self.env.ref("cap_requirements.project_requirement_form_view").id, 'form']],
        }

    def delete_project_requirement_record(self):
        """
        This method unlink particular record of project requirement
        """
        for line in self:
            line.unlink()
        return True

    def export_project_requirment(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Project Requirement')
        style_center = xlwt.easyxf("font: bold 1, color black; align: horiz center")
        data_center = xlwt.easyxf("align: horiz center")
        # Add Header
        if len(self.project_id.partner_id) > 1:
            raise ValidationError('Multiple project requirements can not be export at a time!')
        if self.project_id.partner_id.lang == 'fr_FR':
            headers = [_('Domaine du projet'), _('Nom'), _('Description'), _('Phase'), _('Maturité'), _('Utilisée'),
                       _('Temps estimé'), _('Coût du module'), _('Fonctionnalités non abordées lors des préventes'),
                       _('Comment cela se fera'), _('Livrable du client'),
                       _('Rôle')]
        else:
            headers = [_('Project Domain'), _('Name'), _('Description'), _('Phase'), _('Maturity'), _('Used'),
                       _('Estimate Time'), _('Module Cost'), _('Features Not Discussed In Pre Sales'),
                       _('How It Will Be Done'), _('Deliverable From The Customer'),
                       _('Role')]

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, style_center)
        # Add Data
        remove_tag = re.compile('<.*?>')
        for row_num, record in enumerate(self):
            record = record.with_context(lang=record.project_id.partner_id.lang)

            worksheet.write(row_num + 1, 0, record.default_domain_id.name if record.default_domain_id else ' ',
                            data_center)
            worksheet.write(row_num + 1, 1, record.name if record.name else ' ')
            worksheet.write(row_num + 1, 2, re.sub(remove_tag, '', record.description) if record.description else
            ' ')
            worksheet.write(row_num + 1, 3, record.phase_id.name if record.phase_id else ' ', data_center)
            worksheet.write(row_num + 1, 4, record.maturity if record.maturity else ' ', data_center)
            worksheet.write(row_num + 1, 5, record.used.title() if record.used else ' ', data_center)
            worksheet.write(row_num + 1, 6,
                            round(record.estimate_time, 2) if record.used == 'yes' or record.used == False else 0,
                            data_center)
            worksheet.write(row_num + 1, 7, record.module_cost if record.module_cost else ' ', data_center)
            worksheet.write(row_num + 1, 8, record.features_not_discussed_in_pre_sales
            if record.features_not_discussed_in_pre_sales else ' ', data_center)
            worksheet.write(row_num + 1, 10, re.sub(remove_tag, '',
                                                   record.deliverable_from_the_customer) if record.deliverable_from_the_customer else
            ' ')
            worksheet.write(row_num + 1, 11, record.role_id.name if record.role_id else ' ', data_center)

        # Save the workbook to a BytesIO object
        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        # Create a binary file attachment
        attachment_vals = {
            'name': f"{'ProjectRequirement'}.xls",
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'id': self.ids,
        }
        attachment = self.env['ir.attachment'].create(attachment_vals)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
