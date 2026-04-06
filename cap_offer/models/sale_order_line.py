from odoo import fields, models, _, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('order_id', 'product_template_id.skip_for_sale_ok', 'product_template_id', 'product_id',
                 'product_id.product_tmpl_id.skip_for_sale_ok','order_id.offer_id')
    def _compute_skip_product_template_id_domain(self):
        res = super(SaleOrderLine, self)._compute_skip_product_template_id_domain()
        for rec in self:
            if rec.order_id.offer_id:
                offer_skip_template_ids = self.env['product.template'].search([
                    ('offer_ids', '!=', rec.order_id.offer_id.id)
                ])
                current_templates = self.env['product.template'].with_company(self.env.company).search([
                    ('skip_for_sale_ok', '=', True),
                    '|',
                    ('company_id', '=', False),
                    ('company_id', '=', self.env.company.id)
                ])
                final_skip_templates = current_templates + offer_skip_template_ids
                rec.skip_product_template_id_domain = final_skip_templates
        return res