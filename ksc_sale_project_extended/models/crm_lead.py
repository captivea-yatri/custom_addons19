from odoo import api, models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    est_user = fields.Integer(string='Estimated number of Users')
    est_hours = fields.Integer(string='Estimated Hours for MVP')
    x_studio_win_date = fields.Datetime('Win Date', compute="compute_x_studio_win_date", store=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', check_company=True, index=True, tracking=10,
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.",
        domain=lambda self:[('id','not in',self.env['res.company'].sudo().search([('partner_id', '!=', False)]).partner_id.ids),
                            ('id','not in',self.env['res.company'].sudo().search([('partner_id', '!=', False)]).partner_id.child_ids.ids)])

    @api.depends('probability', 'date_closed')
    def compute_x_studio_win_date(self):
        """Compute the value of `x_studio_win_date` based on the lead's probability.

    When the probability reaches 100%, this method sets `x_studio_win_date`
    equal to the lead's `date_closed`. Otherwise, the field is reset to False."""
        for record in self:
            if record['probability'] == 100:
                record['x_studio_win_date'] = record['date_closed']
            else:
                record['x_studio_win_date'] = False

    @api.model_create_multi
    def create(self, vals):
        """Override of the base create method to ensure all new CRM leads
    are automatically classified as opportunities.
"""
        rec = super(CrmLead, self).create(vals)
        rec['type'] = 'opportunity'
        return rec
