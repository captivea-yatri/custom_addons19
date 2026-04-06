# -*- coding: utf-8 -*-

from odoo import models, fields, api

_TEL_CHARS_TO_REMOVE = [' ', '.', '/', '-']


class Project(models.Model):
    _inherit = 'project.project'

    project_status_id = fields.Many2one('project.status', string='Project Status', copy=False, tracking=True)
    code = fields.Char(string="Code", related="project_status_id.code")


class ProjectTask(models.Model):
    _inherit = 'project.task'

    project_status_id = fields.Many2one('project.status', related="project_id.project_status_id",
                                        string="Status", store=True)
    code = fields.Char(string="Code", related="project_status_id.code")


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    project_status_id = fields.Many2one('project.status', string="project status at time logged")

    @api.model_create_multi
    def create(self, vals_list):
        """
        This method is used to set project status based on project's status
        """
        for vals in vals_list:
            project_id = self.env['project.project'].browse(vals.get('project_id'))
            vals.update({
                'project_status_id': project_id.project_status_id.id
            })
        return super(AnalyticLine, self).create(vals_list)
