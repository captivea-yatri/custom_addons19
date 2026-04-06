from odoo import fields, models, api, _
import datetime
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    def _get_default_offer_id(self):
        sale_order_id = self.env['sale.order'].browse(self._context.get('active_id')) if self._context.get('active_id') else False
        if sale_order_id:
            return sale_order_id.offer_id

    offer_id = fields.Many2one('offer.offer', string='Offer', store=True,default=_get_default_offer_id, tracking=True)
    filtered_offer_ids = fields.Many2many('offer.offer',compute="_compute_filtered_offer_ids")

    @api.depends('sale_order_ids')
    def _compute_filtered_offer_ids(self):
        for rec in self:
            rec.filtered_offer_ids = [(6, 0, rec.sale_order_ids.mapped('offer_id').ids)]

    default_domain_ids = fields.Many2many('default.domain', 'project_default_domain_rel', 'project_id', 'domain_id',
                                          domain="[('id', 'in', filtered_default_domain_ids),('all_phases', '=', False)]",
                                          string='Default Domain', tracking=True)
    filtered_default_domain_ids = fields.Many2many('default.domain', compute='_compute_filtered_default_domain_ids',
                                                   string='Filtered Default Domain IDs')

    @api.depends('sale_order_ids')
    def _compute_filtered_default_domain_ids(self):
        """
        Filter the all domain from each sale order product default domain.
        """
        for project in self:
            if (project.create_date and project.company_id.allow_offer_date and
                    project.create_date.date() >= project.company_id.allow_offer_date and project.offer_id):
                if project.offer_id.restrict_time:
                    order_line = project.sale_order_ids.mapped('order_line')
                    project.filtered_default_domain_ids = [(6, 0, order_line.product_id.default_domain_ids.ids)]
                elif not project.offer_id.restrict_time:
                    default_domain_ids = self.env['default.domain'].search([('offer_ids', 'in', project.offer_id.ids)])
                    project.filtered_default_domain_ids = [(6, 0, default_domain_ids.ids)]
            else:
                project.filtered_default_domain_ids = [(6, 0, self.env['default.domain'].search([]).ids)]

    # @api.depends('sale_order_line_ids')
    # def _compute_offer_from_so_order(self):
    #     for project in self:
    #         if (project.create_date and project.company_id.allow_offer_date and
    #                 project.create_date.date() >= project.company_id.allow_offer_date):
    #             product_offer_ids = project.sale_order_line_ids.mapped('product_id.offer_ids')
    #             if product_offer_ids:
    #                 combined_offer_ids = self.env['offer.offer'].search([
    #                     ('combined_offer_ids', 'in', product_offer_ids.ids)])
    #                 for offer in combined_offer_ids:
    #                     if sorted(offer.combined_offer_ids.ids) == sorted(product_offer_ids.ids):
    #                         project.offer_id = offer.id
    #                 if not project.offer_id:
    #                     final_min = min(product_offer_ids.mapped('sequence'))
    #                     min_sequence_offer_id = product_offer_ids.filtered(lambda seq: seq.sequence == final_min)
    #                     if len(min_sequence_offer_id) > 1:
    #                         raise ValidationError(
    #                             'Found multiple offer with same sequence, please rearrange offers once!')
    #                     project.offer_id = min_sequence_offer_id.id
    #             else:
    #                 project.offer_id = False
    #         else:
    #             project.offer_id = project.offer_id or False
