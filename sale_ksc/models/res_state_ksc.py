from odoo.exceptions import ValidationError
from odoo import models, fields, api

class ResStateKsc(models.Model):
    _name = 'res.state.ksc'
    _description = 'State'

    name = fields.Char(required=True)
    state_code = fields.Char(required=True, string='State Code')
    country_id = fields.Many2one('res.country.ksc', string='Country')

    @api.constrains('state_code')
    def _check_unique_state_code(self):
        """Ensure state_code is unique"""
        for rec in self:
            dup = self.search([
                ('state_code', '=', rec.state_code),
                ('id', '!=', rec.id)
            ], limit=1)
            if dup:
                raise ValidationError(f"State code '{rec.state_code}' must be unique!")
