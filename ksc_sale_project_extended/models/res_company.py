from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    yearly_increase_rate = fields.Float('Yearly Increase Rate', tracking=True)

    @api.constrains('yearly_increase_rate')
    def _verify_yearly_increase_rate(self):
        """Ensure the yearly increase rate is valid.

    This constraint validates that the field `yearly_increase_rate`
    is not negative. If a negative value is detected, a ValidationError
    is raised to prevent saving the record."""
        for order in self:
            if order.yearly_increase_rate < 0:
                raise ValidationError(_("The increase rate should be greater than zero!"))
