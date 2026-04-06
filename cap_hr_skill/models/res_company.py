# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    limitation_of_skill_request = fields.Integer(string="Limitation Of Skill Request", default=3)

    @api.constrains('limitation_of_skill_request')
    def check_limitation_of_skill_request(self):
        """
               Ensure the limitation of skill requests is greater than zero.
        """
        for rec in self:
            if rec.limitation_of_skill_request <= 0:
                raise ValidationError('Limitation of skill request must be greater than 0!')
