# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from bs4 import BeautifulSoup


class Partner(models.Model):
    _inherit = 'res.company'

    maintenance_support_terms = fields.Html(string='Maintenance Support Terms', translate=True)
    number_of_days_authorized_in_late = fields.Integer(string='Number of days authorized in late')

    @api.constrains('number_of_days_authorized_in_late')
    def _check_number_of_days_authorized_in_late(self):
        """Validate that the authorized late days value is non-negative."""
        if self.number_of_days_authorized_in_late < 0:
            raise ValidationError(_('Number of days authorized in late is must be positive number!!!'))