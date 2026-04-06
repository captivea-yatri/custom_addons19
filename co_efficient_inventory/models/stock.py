# -*- coding: utf-8 -*-

from odoo import models, fields, api
            

class Quant(models.Model):
    """ Quants are the smallest unit of stock physical instances """
    _inherit = "stock.quant"

    product_categ_id = fields.Many2one('product.category', compute='_compute_product_categ_id', related=False, store=True)

    @api.depends('product_id.product_tmpl_id.categ_id')
    def _compute_product_categ_id(self):
        """
        While changing Product category in product template, value of product category for quant is fetched from its product variant record
        :return:
        """
        for quant in self:
            quant.product_categ_id = quant.product_id.categ_id.id
