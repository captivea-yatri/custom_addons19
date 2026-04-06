from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    offer_id = fields.Many2one('offer.offer', string='So Offer',domain="[('id', 'in', filtered_offer_ids)]")
    business_unit_id = fields.Many2one('business.unit',string="Business Unit")
    business_localisation_id = fields.Many2one('business.localisation',string="Business Localisation",store = True)
    filtered_offer_ids = fields.Many2many('offer.offer', compute='_compute_offer_ids')
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_pricelist_id',
        store=True, readonly=False, precompute=True, check_company=True,  # Unrequired company
        tracking=1,
        domain="[('id', 'in', filtered_pricelist_ids)]",
        help="If you change the pricelist, only newly added lines will be affected.")
    filtered_pricelist_ids = fields.Many2many('product.pricelist', compute='_compute_pricelist_ids')
    use_offer = fields.Boolean(string='Use Offer', compute='_compute_use_offer')

    @api.depends('company_id')
    def _compute_use_offer(self):
        for rec in self:
            if rec.company_id.use_offer:
                rec.use_offer = True
            else:
                rec.use_offer = False

    @api.depends('business_localisation_id')
    def _compute_pricelist_id(self):
        """
        As per our updated functionality if there is only one record for pricelist on business localisation we set it on sales order.
        """
        for order in self:
            if order.use_offer:
                if order.state != 'draft':
                    continue
                if not order.business_localisation_id or not order.business_localisation_id.pricelist_ids:
                    order.pricelist_id = False
                    continue
                pricelists_ids = order.business_localisation_id.pricelist_ids.filtered(lambda p: p.company_id == order.company_id)
                if pricelists_ids:
                    order.pricelist_id = pricelists_ids[0] if len(pricelists_ids) == 1 else False
                else:
                    order.pricelist_id = False
            else:
                return super(SaleOrder, self)._compute_pricelist_id()

    @api.onchange('business_unit_id','business_localisation_id')
    def _onchange_bu_bl_id(self):
        for rec in self:
            rec.offer_id = False
            rec._compute_pricelist_id()

    @api.onchange('offer_id')
    def _onchange_offer_id(self):
        for rec in self:
            rec.sale_order_template_id = False

    @api.depends('business_localisation_id')
    def _compute_pricelist_ids(self):
        for rec in self:
            rec.filtered_pricelist_ids = rec.business_localisation_id.pricelist_ids if rec.business_localisation_id.pricelist_ids else self.env['product.pricelist'].search(['|', ('company_id', '=', rec.company_id.id), ('company_id', '=', False)])

    @api.depends('business_unit_id', 'business_localisation_id')
    def _compute_offer_ids(self):
        """
        Filter all offers where Business Unit OR Business Localisation matches.
        """
        Offer = self.env['offer.offer']
        for order in self:
            domain = []
            bu = order.business_unit_id.id
            loc = order.business_localisation_id.id

            if bu and loc:
                # OR condition between both fields
                domain = ['&',
                          ('business_unit_ids', 'in', bu),
                          ('business_localisation_ids', 'in', loc)
                          ]
            elif bu:
                domain = [('business_unit_ids', 'in', bu)]
            elif loc:
                domain = [('business_localisation_ids', 'in', loc)]
            else:
                domain = []  # no filters

            offers = Offer.search(domain) if domain else Offer.browse()
            order.filtered_offer_ids = offers

    def _validate_product_quantity(self):
        for order in self:
            if order.offer_id.restrict_time == True:
                po_restrict_time_false = order.order_line.filtered(
                    lambda so_line: so_line.product_id.offer_ids.filtered(lambda offer:offer.restrict_time == False))
                po_restrict_time_true = order.order_line.filtered(
                    lambda product: product.product_id.offer_ids.filtered(lambda offer:offer.restrict_time == True))

                common_lines = po_restrict_time_false & po_restrict_time_true
                if len(common_lines) > 0 and po_restrict_time_false != po_restrict_time_true:
                    quantity_restrict_time_false = sum(common_lines.mapped('product_uom_qty'))
                    if (self._context.get('product_quantity', False) and common_lines and po_restrict_time_true and
                            quantity_restrict_time_false > 25):
                        raise ValidationError('When order lines have offers with restrict time True as well as with False :\n'
                                              'Please make sure maximum quantity should not be more then 25 for line that have '
                                              'offer with restrict time False.')

    @api.model_create_multi
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if (order.create_date and order.company_id.allow_offer_date and
                order.create_date.date() >= order.company_id.allow_offer_date):
            order.with_context(product_quantity=True)._validate_product_quantity()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for so in self:
            if so.company_id.allow_offer_date and so.create_date and so.create_date.date() >= so.company_id.allow_offer_date:
                so.with_context(product_quantity=True)._validate_product_quantity()
            if vals.get('offer_id'):
                if len(so.order_line) > 0:
                    raise ValidationError('Please remove all sale order lines to change offer on sale order !!')
        return res

    # @api.depends('order_line')
    # def _compute_so_offer(self):
    #     for order in self:
    #         if (order.create_date and order.company_id.allow_offer_date and
    #                 order.create_date.date() >= order.company_id.allow_offer_date):
    #                 product_offer_ids = order.order_line.mapped('product_id.offer_id')
    #                 if product_offer_ids:
    #                     combined_offer_ids = self.env['offer.offer'].search([
    #                         ('combined_offer_ids', 'in', product_offer_ids.ids)])
    #                     for offer in combined_offer_ids:
    #                         if sorted(offer.combined_offer_ids.ids) == sorted(product_offer_ids.ids):
    #                             order.offer_id = offer.id
    #                     if not order.offer_id:
    #                         final_min = min(product_offer_ids.mapped('sequence'))
    #                         min_sequence_offer_id = product_offer_ids.filtered(lambda seq: seq.sequence == final_min)
    #                         if len(min_sequence_offer_id) > 1:
    #                             raise ValidationError('Found multiple offer with same sequence, '
    #                                                   'please rearrange offers once!')
    #                         order.offer_id = min_sequence_offer_id.id
    #                 else:
    #                     order.offer_id = False
    #         else:
    #             order.offer_id = False
