# -*- coding: utf-8 -*-

from odoo import models, fields, api


class product_currency(models.Model):
    _name = 'product_currency.product_currency'

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

    """
     This method is used to convert in float value and divide the value of field value
    """

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100
