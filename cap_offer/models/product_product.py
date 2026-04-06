from odoo import fields, models, api, _, Command
from odoo.exceptions import ValidationError



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    offer_ids = fields.Many2many('offer.offer','rel_product_template_offer','product_template_id','offer_id',string="Offers", tracking=True)
    default_domain_ids = fields.Many2many('default.domain', 'default_domain_ref', 'product_id', 'offer_id',
                                          string='Default Domain', tracking=True)

    # @api.constrains('offer_ids')
    # def _check_offer_restrict_time(self):
    #     for product in self:
    #         if not product.offer_ids:
    #             continue
    #
    #         # Get distinct restrict_time values among related offers
    #         restrict_values = product.offer_ids.mapped('restrict_time')
    #
    #         # If there are both True and False values, raise an error
    #         if len(set(restrict_values)) > 1:
    #             raise ValidationError(_(
    #                 "You cannot assign offers with both restricted and non-restricted time "
    #                 "to the same product.\n\n"
    #                 "Please select either all restricted-time or all non-restricted-time offers."
    #             ))

    def _mail_track(self, tracked_fields, initial_values):
        changes, tracking_value_ids = super()._mail_track(tracked_fields, initial_values)
        # Many2many tracking
        if len(changes) > len(tracking_value_ids):
            for changed_field in changes:
                if tracked_fields[changed_field]['type'] in ['one2many', 'many2many']:
                    field = self.env['ir.model.fields']._get(self._name, changed_field)
                    vals = {
                        'field': field.id,
                        'field_desc': field.field_description,
                        'field_type': field.ttype,
                        'tracking_sequence': field.tracking,
                        'old_value_char': ', '.join(initial_values[changed_field].mapped('name')),
                        'new_value_char': ', '.join(self[changed_field].mapped('name')),
                    }
                    tracking_value_ids.append(Command.create(vals))
        return changes, tracking_value_ids


class ProductProduct(models.Model):
    _inherit = 'product.product'

    offer_ids = fields.Many2many('offer.offer', 'rel_product_offer', 'product_id', 'offer_id',
                                 string="Offers",related='product_tmpl_id.offer_ids', tracking=True)
    default_domain_ids = fields.Many2many('default.domain', string='Default Domain',
                                          related='product_tmpl_id.default_domain_ids', tracking=True)
