from odoo import models, api, fields
from odoo.exceptions import AccessError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    website_id = fields.Many2one(comodel_name='website',string='From website',copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        """ This method is used for set company and team based on default_crm_lead_config Country."""
        for value in vals_list:
            if self.env.context.get('website_id'):
                value.update({'website_id' : self.env.context.get('website_id'),})
                crm_lead_config_id = self.env['default.crm.lead.config'].sudo().search(
                    [('country_id', '=', value.get('country_id')), ('website_id', '=', self.env.context.get('website_id'))])
                if crm_lead_config_id:
                    value.update({
                        'company_id': crm_lead_config_id.company_id.id,
                        'team_id': crm_lead_config_id.team_id.id
                    })
        return super(CrmLead, self).create(vals_list)

    def write(self, vals):
        """ This method is used for set company and team based on default_crm_lead_config Country."""

        ############################
        # TODO: Need to remove this code after florentin complated his N8N task.
        if self.env.user.has_group('__export__.res_groups_494_18ed28a7'):
            raise AccessError('You are not authorized to update this Opportunity!!')
        ############################


        res = super(CrmLead, self).write(vals)
        for rec in self:
            if rec.team_id or vals.get('team_id') or rec.user_id or not rec.website_id:
                continue

            company_id = vals.get('company_id') if isinstance(vals.get('company_id'), int) else vals.get(
                'company_id').id if vals.get('company_id') else None
            country_id = vals.get('country_id') if isinstance(vals.get('country_id'), int) else vals.get(
                'country_id').id if vals.get('country_id') else rec.country_id.id if rec.country_id else None
            website_id = rec.website_id.id if rec.website_id else None

            if company_id and country_id:
                crm_lead_config = self.env['default.crm.lead.config'].sudo().search([
                    ('country_id', '=', country_id),
                    ('company_id', '=', company_id),
                    ('website_id', '=', website_id)
                ], limit=1)

                if crm_lead_config:
                    rec.team_id = crm_lead_config.team_id.id

        return res
