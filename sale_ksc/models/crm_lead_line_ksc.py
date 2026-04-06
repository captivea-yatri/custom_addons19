from odoo import models, fields, api

class CrmLeadLineKsc(models.Model):
    _name = 'crm.lead.line.ksc'
    _description = 'CRM Lead Line KSC'

    product_id = fields.Many2one('product.ksc', string="Product")
    name = fields.Char(string="Description")
    expected_sell_qty = fields.Float(string="Expected Qty")
    uom_id = fields.Many2one('product.uom.ksc', string="UOM")
    lead_id = fields.Many2one('crm.lead.ksc', string="Lead")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.name = rec.product_id.name if rec.product_id else False
