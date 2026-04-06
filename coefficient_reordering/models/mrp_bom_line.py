# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    def _get_product_reordering_ids(self):
        """
           This method calculates the reordering rules for the product based on its order points,
           if the reordering rule are set then it shows in 'reordering_rules' field.
           If there are no order points, it sets the value of 'reordering_rules' to False.
           """
        for line in self:
            line.reordering_rules = ",".join(
                line.product_id.orderpoint_ids.mapped("name")) if line.product_id.orderpoint_ids else False

    reordering_rules = fields.Char(compute=_get_product_reordering_ids, string="Reordering Rule")
