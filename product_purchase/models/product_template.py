# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    # _name = 'product.templates'
    _inherit = 'product.template'

    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchases')

    def _purchase_count(self):
        for template in self:
            # template.purchase_count = sum([p.purchase_count for p in template.product_variant_ids])
            all_related_lines = self.env['purchase.order.line'].search(
                [('product_id', '=', template.product_variant_id.name), ('state', 'in', ['purchase', 'done'])])
            print('all_related_lines', all_related_lines, all_related_lines.order_id, len(all_related_lines))
            template.purchase_count = len(all_related_lines)
        return True
