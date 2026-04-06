# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ResLang(models.Model):
    _inherit = 'res.lang'

    alt_language = fields.Many2one('res.lang', 'Alternative Language To Load Translation')
