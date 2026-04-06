from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAccountRestriction(models.Model):
    _name = 'product.account.restriction'
    _description = 'Product Account Restriction'

    name = fields.Char('Name', related="partner_id.name")
    partner_id = fields.Many2one('res.partner', string="Partner")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company,
                                 domain=lambda self: [('id', 'in', self.env.context.get('allowed_company_ids', []))])
    allowed_product_ids = fields.Many2many('product.product', string="Allowed Product",
                                           domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    allowed_account_ids = fields.Many2many('account.account', string="Allowed Account",
                                           domain="['|', ('company_ids', '=', False), ('company_ids', 'in', [company_id])]")

    @api.constrains('partner_id', 'company_id')
    def _check_model_name(self):
        """
        This method is used to create unique partner
        """
        rec = self.search(
            [('id', '!=', self.id), ('partner_id', '=', self.partner_id.id), ('company_id', '=', self.company_id.id)])
        if rec:
            raise ValidationError(
                _("Partner {} Already Exists with Company {}".format(self.partner_id.name, self.company_id.name)))
