# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class DefaultDomain(models.Model):
    _inherit = 'default.domain'

    used_on_opportunities = fields.Boolean(string="Used On Opportunities")

    @api.constrains('used_on_opportunities')
    def _check_interested_domain(self):
        """
            Prevent disabling a domain that's already linked to CRM opportunities.

            When 'used_on_opportunities' is modified, this constraint checks if any
            CRM Lead/Opportunity references the domain in 'interested_domain_ids'.
            If found, a ValidationError is raised to ensure the domain is unlinked
            before being disabled.
            """
        if self.env['crm.lead'].search([('interested_domain_ids', 'in', self.ids)]):
            raise ValidationError('Domain is already configured on opportunity, Please remove the configuration first.')

    def unlink(self):
        """
           Prevent deletion of a domain that is still linked to CRM opportunities.

           Before deleting a Default Domain record, this method checks if it is
           referenced in any CRM Lead/Opportunity through the 'interested_domain_ids'
           field. If such a link exists, a ValidationError is raised to ensure
           the domain is unlinked before deletion.
           """
        for domain in self:
            if self.env['crm.lead'].search([('interested_domain_ids', '=', domain.id)]):
                raise ValidationError('Domain is already configured on opportunity, '
                                      'Please remove the configuration first.')
        return super(DefaultDomain, self).unlink()
