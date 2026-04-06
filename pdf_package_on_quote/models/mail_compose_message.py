from odoo import _, api, fields, models, tools, Command

class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.depends('composition_mode', 'model', 'res_domain', 'res_ids', 'template_id')
    def _compute_attachment_ids(self):
        """
               Compute attachments for the mail composer.

               Adds attachments from pricelist items of products in a sale order
               when the composer is opened from a sale order. Ensures PDFs or
               files linked to pricelist items are automatically included in
               quotation emails.
        """
        super()._compute_attachment_ids()
        for composer in self:
            if composer._context.get('active_id') and composer._context.get('active_model') == 'sale.order':
                search_sale_order = self.env['sale.order'].browse(composer._context.get('active_id'))
                pricelist = search_sale_order.pricelist_id
                if pricelist and pricelist.item_ids and pricelist.item_ids.mapped('product_tmpl_id'):
                    all_products_from_pricelists = pricelist.item_ids.mapped('product_tmpl_id')
                    for line in search_sale_order.order_line:
                        if line.product_template_id in all_products_from_pricelists:
                            required_item_ids = pricelist.item_ids.filtered(lambda x: x.product_tmpl_id == line.product_template_id)
                            for required_item_id in required_item_ids:
                                if required_item_id.attachment_id:
                                    composer.attachment_ids |= required_item_id.attachment_id
