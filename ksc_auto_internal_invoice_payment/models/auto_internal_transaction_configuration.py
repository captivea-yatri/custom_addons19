
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class AutoInternalTransactionConfiguration(models.Model):
    _name = "auto.internal.transaction.configuration"
    _description = "Auto Internal Transaction Configuration"
    _rec_name = 'partner_id'

    company_id = fields.Many2one(comodel_name='res.company', string="Company")
    journal_id = fields.Many2one(comodel_name='account.journal', string="Account Journal", check_company=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), "
                                        "('type', 'in', ['cash', 'bank'])]")
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer")

    @api.constrains('company_id', 'partner_id')
    def unique_partner_company_constraint(self):
        """Ensure each company-partner combination is unique."""
        for rec in self:
            auto_trans_config_id = rec.search([('company_id', '=', rec.company_id.id),
                                               ('partner_id', '=', rec.partner_id.id), ('id', '!=', rec.id)])
            if auto_trans_config_id:
                raise ValidationError("Configuration must be Unique company / customer!")

