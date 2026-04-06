# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_studio_product_to_receive = fields.Boolean('Product To Receive')
    minimumSalePrice = fields.Float("Minimum Sale Price", company_dependent=True)
    skip_for_sale_ok = fields.Boolean('Skip On Sale Order', company_dependent=True)
    emp_filter_domain = fields.Char(string='Limited To Employee')
    restrict_description_modification = fields.Boolean(string='Restrict Description Modification')
    skip_for_so_line_id = fields.Many2one('sale.order.line')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_studio_product_to_receive_1 = fields.Boolean('Product To Receive',
                                                   related='product_tmpl_id.x_studio_product_to_receive')
    skip_for_so_line_id = fields.Many2one('sale.order.line')
    restrict_description_modification = fields.Boolean(string='Restrict Description Modification', related='product_tmpl_id.restrict_description_modification')
