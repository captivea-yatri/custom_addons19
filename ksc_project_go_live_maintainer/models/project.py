# -*- coding: utf-8 -*-

from odoo import api, models, fields


class Project(models.Model):
    _inherit = "project.project"

    x_studio_go_live_date = fields.Date(copy=False, tracking=True, readonly=True)
    glive_change_request_ids = fields.One2many('glive.change.request', 'project_id', string='Go Live Change Request',
                                               copy=False)

    def action_view_go_live_cr(self):
        """
               This method is used to display all 'Go Live Change Request' records associated with
               a specific project. It is typically triggered by a smart button or related action
               from the project form view.
           """
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('ksc_project_go_live_maintainer.action_view_glive_change_request')
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id, 'from_project_action': True}
        go_live_crrs = self.env['glive.change.request'].search([('project_id', '=', self.id)])
        if not self.env.context.get('from_embedded_action', False) and len(go_live_crrs) == 1:
            action['views'] = [[False, 'form']]
            action['res_id'] = go_live_crrs.id
        return action
