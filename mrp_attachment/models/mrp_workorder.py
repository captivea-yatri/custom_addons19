# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def action_all_next(self):
        '''
        Automate remaining operations until quantity is zero while performing next consecutive operations
        '''
        while self.qty_remaining > 0:
            while self.current_quality_check_id:
                self.current_quality_check_id.action_next()
            self.record_production()
