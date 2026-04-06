# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'

    use_default_stages = fields.Boolean(string="Use Default Swim Lanes", default=True)
    type_id = fields.Many2one('project.type',string='Type')
    template_id = fields.Many2one('project.project', domain="[('type_id.name','=','Template')]", string="Template")

    def go_use_default_stages(self):
        '''
        Assigning project id to the stages which have 'is_default' true
         '''
        default_stages = self.env['project.task.type'].search([('is_default','=',True)])
        default_stages.write({'project_ids':[(4,self.id,False)]})

    def go_use_project_template(self):

        ''' Fetching task stages from the template, assigning it to newly created project
        fetching existing task's value from template and creating new tasks for newly created project'''

        default_stages = self.env['project.task.type'].search([('project_ids','in',[self.template_id.id])])
        default_stages.write({'project_ids':[(4,self.id,False)]})
        for task in self.template_id.task_ids:
            new_task_vals = {
                        'name': task.name,
                        'description': task.description,
                        'stage_id': task.stage_id.id,
                        'project_id': self.id,
                        'sequence': task.sequence,
                    }
            self.env['project.task'].create(new_task_vals)

    @api.model
    # @api.returns('self', lambda rec: rec.id)
    @api.model
    def create(self, vals_list):
        """
        Override create to handle template or default stages for multiple records.
        """
        # If a single dict is passed, convert it to a list
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        # Create the records using super
        records = super(Project, self).create(vals_list)

        # Loop over each record and corresponding vals
        for rec, vals in zip(records, vals_list):
            if vals.get('template_id'):
                rec.go_use_project_template()
            elif vals.get('use_default_stages'):
                rec.go_use_default_stages()

        return records

    def write(self, vals):
        '''
        for existing project if template is selected then fetching task stages and assign them to existing project,
        and creating new tasks by fetching values from template's tasks
        '''
        rec = super(Project, self).write(vals)
        if vals.get('template_id'):
            self.go_use_project_template()
        return rec
