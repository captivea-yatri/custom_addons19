# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProjectType(models.Model):
    _name = 'project.type'

    name = fields.Char(string="Type")
