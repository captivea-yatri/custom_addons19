from odoo import fields, models, api

class ProdPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    pdf_file = fields.Binary(string='Upload Document')
    pdf_file_name = fields.Char(string='File name')
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')

    @api.model_create_multi
    def create(self, vals_list):
        """Create pricelist items and convert uploaded PDFs into attachments."""
        records = super().create(vals_list)
        for rec in records:
            if rec.pdf_file:
                attachment_name = rec.pdf_file_name or f"Pricelist_Item_{rec.id}.pdf"
                attachment = self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'datas': rec.pdf_file,
                    'res_model': 'product.pricelist.item',
                    'res_id': rec.id,
                    'type': 'binary',
                })
                rec.attachment_id = attachment.id
        return records

    def write(self, values):
        """Update pricelist items and manage PDF attachments."""
        res = super().write(values)
        for rec in self:
            # Create attachment if new PDF is uploaded
            if values.get('pdf_file'):
                attachment_name = rec.pdf_file_name or f"Pricelist_Item_{rec.id}.pdf"
                attachment = self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'datas': rec.pdf_file,
                    'res_model': 'product.pricelist.item',
                    'res_id': rec.id,
                    'type': 'binary',
                })
                rec.attachment_id = attachment.id
            # Remove attachment if PDF is cleared
            elif 'pdf_file' in values and not values.get('pdf_file'):
                if rec.attachment_id:
                    rec.attachment_id.unlink()
        return res
