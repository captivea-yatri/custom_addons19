from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order.template'

    offer_ids = fields.Many2many('offer.offer','rel_sale_order_template_offer','offer_id','sale_order_template_id',string="Offers")