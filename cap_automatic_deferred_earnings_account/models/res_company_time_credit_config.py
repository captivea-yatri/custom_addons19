from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TimeCredit(models.Model):
    _name = 'res.company.time.credit.config'
    _description = 'Time Credit Account Configuration'


    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    revenue_account = fields.Many2one('account.account', string='Revenue Account',
                                      domain="['|', ('company_ids', '=', False), ('company_ids', 'in', [company_id])]",
                                      required=True)
    revenue_income_account = fields.Many2one('account.account', string='Deferred Revenue Account',
                                             domain="['|', ('company_ids', '=', False), ('company_ids', 'in', [company_id])]"
                                             , required=True)
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 required=True)

    @api.constrains('company_id', 'revenue_account', 'revenue_income_account','journal_id')
    def _check_unique_combination(self):
        ''' Ensure that each company has a unique combination of revenue_account, revenue_income_account and journal_id '''
        for record in self:
            # Search for records with the same company_id, revenue_account, and revenue_income_account
            existing_records = self.search([
                ('company_id', '=', record.company_id.id),
                ('revenue_account', '=', record.revenue_account.id),
                ('revenue_income_account', '=', record.revenue_income_account.id),
                ('journal_id','=',record.journal_id.id),
                ('id', '!=', record.id)  # Exclude the current record
            ])
            if existing_records:
                raise ValidationError(_(
                    'Each company should have a unique combination of revenue and deferred revenue account and journal.'
                    ' Duplicate found for Company "%s", Revenue Account "%s", Deferred Revenue Account "%s" '
                    'and journal "%s".') % (record.company_id.name, record.revenue_account.name,
                                            record.revenue_income_account.name, record.journal_id.name))
