# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    linked_project = fields.Boolean(default=False, copy=False, compute='compute_linked_project', store=True)
    total_remaining_qty = fields.Float('Total Remaining Quantity', compute='_calculate_total_remaining_qty',
                                       store=True,
                                       help="Counts the remaining quantity of only sale order lines where the product is prepaid and the product to received is marked as true.")
    require_signature = fields.Boolean(
        string="Online Signature",
        compute='_compute_require_signature',
        store=True, readonly=False, precompute=True, tracking=True,
        help="Request a online signature and/or payment to the customer in order to confirm orders automatically.")
    disable_increase_rate = fields.Boolean('Disable Increase Rate', copy=False)
    increase_rate = fields.Float('Increase Rate', copy=False, readonly=False, store=True, tracking=True)
    last_update_date = fields.Date('Last Update Date', copy=False, readonly=True)
    next_update_date = fields.Date('Next Update Date', copy=False, readonly=True)

    @api.constrains('increase_rate')
    def _verify_increase_rate(self):
        """ Validate the value of the `increase_rate` field.
    This constraint ensures that `increase_rate` is not negative.
    If a negative value is found on any record, a ValidationError is raised
    to prevent the record from being saved."""
        for order in self:
            if order.increase_rate < 0:
                raise ValidationError(_("The increase rate should be greater than zero!"))

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """ Onchange handler for `company_id`.
    When the company is changed, this method automatically updates
    the `increase_rate` field using the company's `yearly_increase_rate`
    value."""
        if self.company_id:
            self.increase_rate = self.company_id.yearly_increase_rate

    @api.model
    def _calculate_increase_unit_price(self):
        """This method is intended to run periodically (e.g., via a cron job).
    It performs the following steps:
        1. Search for sale orders that:
            - Have price increase enabled (`disable_increase_rate = False`)
            - Have a positive `increase_rate`
            - Are in 'sale' state
            - Have reached or passed their `next_update_date`

        2. For each matched sale order, update the unit price of lines
           whose products use the 'delivered_timesheet' service policy.
           The new price is calculated using:
                new_price = old_price * (1 + increase_rate / 100)

        3. Update the sale order's `last_update_date` to today and
           schedule the next update date one year later.

    This logic ensures automatic yearly increment of service prices
    for recurring contracts or long-term service agreements."""
        today = fields.Date.today()
        sale_orders = self.search([
            ('disable_increase_rate', '=', False),
            ('increase_rate', '>', 0),
            ('state', '=', 'sale'),
            ('next_update_date', '<=', today),
        ])

        for order in sale_orders:
            lines = order.order_line.filtered(lambda l: l.product_id.service_policy == 'delivered_timesheet')
            if not lines:
                continue

            for line in lines:
                new_price = line.price_unit * (1 + order.increase_rate / 100)
                line.write({'price_unit': new_price})

            order.write({
                'last_update_date': today,
                'next_update_date': fields.Date.add(today, years=1),
            })

    @api.depends('order_line.x_studio_remaining_quantity')
    def _calculate_total_remaining_qty(self):
        """Compute the total remaining quantity for prepaid service products.
    This method sums the `x_studio_remaining_quantity` of all order lines
    whose products are:
        - of type 'service', and
        - using the 'ordered_prepaid' service policy.
    The computed total is stored in the field `total_remaining_qty`."""
        for rec in self:
            total_remaining_qty = 0
            for line in rec.order_line:
                if line.product_id.type == 'service' and line.product_id.service_policy == 'ordered_prepaid':
                    total_remaining_qty += line.x_studio_remaining_quantity
            rec.write({'total_remaining_qty': total_remaining_qty})

    @api.depends('project_id', 'order_line.project_id')
    def compute_linked_project(self):
        """Compute whether the sale order is linked to a project.
    This method sets the boolean field `linked_project` to True if:
        - The sale order has a project assigned in `project_id`, or
        - Any of its order lines has a project assigned in `project_id`.
    Otherwise, `linked_project` is set to False."""
        for rec in self:
            if rec.project_id or any(rec.order_line.filtered(lambda ol: ol.project_id)):
                rec.linked_project = True
            else:
                rec.linked_project = False

    def update_opportunity_expected_revenue_from_sale_order(self):
        """used to update the opportunity expected revenue based on sale order amount untaxed"""
        for rec in self.filtered(lambda so: so.opportunity_id):
            rec.opportunity_id.sudo().write({'expected_revenue': rec.amount_untaxed})

    @api.model_create_multi
    def create(self, vals):
        """Override the default create method to initialize price-increase fields
    and update linked opportunities.
    Logic performed after creating the sale order:
        1. Initialize yearly update dates
           - If the sale order is created directly in the 'sale' state,
             set:
                 * `last_update_date` = `date_order`
                 * `next_update_date` = one year after `date_order`
        2. Set default increase rate
           - If `increase_rate` is not provided in vals and the company
             has a defined `yearly_increase_rate`, use that rate.
        3. Sync CRM opportunity
           - Calls `update_opportunity_expected_revenue_from_sale_order()`
             to update the opportunity's expected revenue based on
             sale order untaxed amount."""
        rec = super(SaleOrder, self).create(vals)
        if rec.state == 'sale' or 'state' in vals and vals['state'] == 'sale':
            rec.last_update_date = rec.date_order
            rec.next_update_date = fields.Date.add(rec.date_order, years=1)

        if 'increase_rate' not in vals and 'company_id' in vals and rec.company_id.yearly_increase_rate:
            rec.increase_rate = rec.company_id.yearly_increase_rate

        rec.update_opportunity_expected_revenue_from_sale_order()
        return rec

    def copy(self, default=None):
        """Override of the copy method to initialize the increase rate on duplicated records.

    When a sale order is duplicated, this method ensures that the new record
    inherits the company's `yearly_increase_rate` unless an explicit value
    is already provided in the `default` dictionary."""
        default = dict(default or {})
        if 'increase_rate' not in default and self.company_id:
            default['increase_rate'] = self.company_id.yearly_increase_rate or 0.0
        return super().copy(default)

    def write(self, vals):
        """Initializes yearly update dates when the sale order is confirmed and applies the default yearly increase rate from the company if missing.
Monitors remaining prepaid service hours and automatically creates reminder activities when hours drop below 20% or reach zero.
After updating the order, it syncs the expected revenue with the linked CRM opportunity."""
        for rec in self:
            if 'state' in vals and vals['state'] == 'sale':
                date_order = vals.get('date_order') or rec.date_order

                vals['last_update_date'] = date_order.date()
                vals['next_update_date'] = fields.Date.add(date_order, years=1)

            if 'increase_rate' not in vals and 'company_id' in vals and rec.company_id.yearly_increase_rate:
                vals['increase_rate'] = rec.company_id.yearly_increase_rate or 0.0

            #todo:need to check uom category replacement in database
            total_qty = round(sum(rec.order_line.filtered(lambda
                                                              line: line.product_id.type == 'service' and line.product_id.service_policy == 'ordered_prepaid' and line.product_uom_id.name in [
                'Working Time', 'Temps de travail', 'Horario de trabajo']).mapped('x_studio_qty_in_hours')), 2)
            if rec.state in ['sale', 'lock'] and 'total_remaining_qty' in vals:
                if vals.get('total_remaining_qty') > 0 and round(rec.total_remaining_qty, 2) > (
                        .2 * total_qty) and round(vals.get('total_remaining_qty'), 2) <= (.2 * total_qty):
                    activity_ids = self.env['mail.activity'].search(
                        [('summary', '=', 'Contact Client'), ('res_id', '=', rec.id)])
                    if rec.activity_ids.filtered(
                            lambda x: x.summary == 'Contact Client') not in activity_ids and rec.partner_id.user_id:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'res_model_id': self.env.ref('sale.model_sale_order').id,
                            'res_id': rec.id,
                            'user_id': rec.partner_id.user_id.id,
                            'summary': 'Contact Client',
                            'note': 'Consumed hours are at or over 80% of ordered hours for sale order. Please contact the client.'
                        })
                elif vals.get('total_remaining_qty') <= 0 and round(rec.total_remaining_qty, 2) != 0.00:
                    activity_ids = self.env['mail.activity'].search(
                        [('summary', '=', 'Contact Client (Over hours)'), ('res_id', '=', rec.id)])
                    if rec.activity_ids.filtered(
                            lambda x: x.summary == 'Contact Client (Over hours)') not in activity_ids and rec.partner_id.user_id:
                        self.env['mail.activity'].sudo().create({
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'res_model_id': self.env.ref('sale.model_sale_order').id,
                            'res_id': rec.id,
                            'user_id': rec.partner_id.user_id.id,
                            'summary': 'Contact Client (Over hours)',
                            'note': 'Consumed hours have exceeded ordered hours for sale order. Please contact the client.'
                        })

        res = super(SaleOrder, self).write(vals)
        self.update_opportunity_expected_revenue_from_sale_order()
        return res

    def auto_invoice_confirm(self):
        """
        Automatically generate and confirm an invoice for prepaid service orders.
    This method is designed to be called programmatically (e.g., via cron or
    workflow automation) to create and post an invoice when certain
    conditions are met.

    Invoice creation logic:
        - The sale order must not require online payment (`require_payment = False`).
        - No invoice should already exist for its order lines.
        - At least one order line must contain a product with the
          'ordered_prepaid' service policy.
        """
        context = dict(self.env.context)
        context.update({'open_invoices': True, 'active_id': self.id, 'skip_security_deposit': True})
        invoice_exist = any(line.invoice_lines for line in self.order_line)
        if not self.require_payment and not invoice_exist and self.order_line.filtered(
                lambda line: line.product_id.service_policy == 'ordered_prepaid'):
            advance_payment = self.env['sale.advance.payment.inv'].with_context(context).create(
                {'advance_payment_method': 'delivered'})
            inv = advance_payment.with_user(self.user_id).sudo().create_invoices()
            invoice = self.env['account.move']
            if self.subscription_state and not inv.get('res_id') and inv.get('domain'):
                if inv.get('domain')[0][0] == 'id':
                    inv_id = inv.get('domain')[0][2][-1]
                    invoice = self.env['account.move'].browse(int(inv_id))
            elif inv.get('res_id'):
                invoice = self.env['account.move'].browse(int(inv.get('res_id')))
            if invoice:
                invoice.sudo().action_post()
                template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)

                ctx = {'sending_methods': ['email'],
                       'mail_partner_ids': invoice.partner_id.ids,
                       'mail_template_id': template and template.id,
                       }
                wizard = invoice.with_context(ctx).action_invoice_sent()
                self.env['account.move.send.wizard'].with_user(self.user_id).sudo().with_context(wizard).create(
                    {'move_id': invoice.id}).sudo().action_send_and_print()
                ##################################################################################################################################################


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_studio_qty_in_hours = fields.Float('Qty In Hours', compute='_qty_in_hours')
    x_studio_remaining_quantity = fields.Float('Remaining Hours', compute='_remaining_quantity', store=True, copy=False)
    x_studio_consumed_qty = fields.Float('Consumed Hours', copy=False)
    restrict_description_modification = fields.Boolean(string='Restrict Description Modification',
                                                       related='product_id.restrict_description_modification')

    @api.depends('order_id', 'product_template_id.skip_for_sale_ok', 'product_template_id', 'product_id',
                 'product_id.product_tmpl_id.skip_for_sale_ok')
    def _compute_skip_product_template_id_domain(self):
        """ Compute the domain of product templates that should be skipped for selection.

    This method generates a list of product template IDs where the field
    `skip_for_sale_ok` is set to True. The domain is computed per record
    and is restricted to:
        - Templates belonging to the current company, or
        - Global templates (company_id = False)
    The result is stored in `skip_product_template_id_domain`, which is
    typically used to restrict product template selection on sale order lines."""
        for rec in self:
            # Fetch product templates with skip_for_sale_ok=True for the current company
            product_tmpl_ids = self.env['product.template'].with_company(self.env.company).search([
                ('skip_for_sale_ok', '=', True),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', self.env.company.id)
            ])
            rec.skip_product_template_id_domain = product_tmpl_ids.ids if product_tmpl_ids else False

    skip_product_template_id_domain = fields.One2many('product.template', 'skip_for_so_line_id',
                                                      'Product Template Id Domain',
                                                      compute="_compute_skip_product_template_id_domain", store=True)

    product_template_id = fields.Many2one(
        string="Product Template",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        # previously related='product_id.product_tmpl_id'
        # not anymore since the field must be considered editable for product configurator logic
        # without modifying the related product_id when updated.
        domain=[('sale_ok', '=', True), ('id', 'not in', skip_product_template_id_domain)])

    # @api.depends('product_uom_qty', 'product_uom_id', 'product_id')
    # def _qty_in_hours(self):
    #     for record in self:
    #         if record.product_uom_id.name in ['Working Time', 'Temps de travail', 'Horario de trabajo']:
    #             record['x_studio_qty_in_hours'] = record.product_uom_qty * (record.product_uom_id.factor_inv * 8)
    #         else:
    #             record['x_studio_qty_in_hours'] = 0.0

    # @api.depends('product_uom_qty', 'product_id')
    def _qty_in_hours(self):
        # todo:need to check uom category replacement in database

        """ This method checks the unit of measure (UoM) of the product associated with
    the sale order line. If the product's UoM represents hours (e.g., "Hours",
    "Temps de travail", "Horario de trabajo"), the method sets the
    `x_studio_qty_in_hours` field to the line's `product_uom_qty`. Otherwise,
    the field is set to 0.0."""
        for record in self:
            # if record.product_id.uom_id.name in ['Hours', 'Temps de travail', 'Horario de trabajo']:
            #     record['x_studio_qty_in_hours'] = record.product_uom_qty
            # else:
            #     record['x_studio_qty_in_hours'] = 0.0
            if record.product_uom_id.name in ['Working Time', 'Hours']:
                record['x_studio_qty_in_hours'] = record.product_uom_qty * (record.product_uom_id.factor * 8)
            else:
                record['x_studio_qty_in_hours'] = 0.0

    @api.depends('product_uom_qty', 'qty_delivered', 'x_studio_consumed_qty', 'x_studio_qty_in_hours')
    def _remaining_quantity(self):
        """This method calculates the remaining quantity based on:
        remaining = x_studio_qty_in_hours - x_studio_consumed_qty

    The result is rounded to 2 decimals and stored in the
    `x_studio_remaining_quantity` field.

    This value helps track how much service/work is still pending
    when quantities are expressed in hours."""
        for record in self:
            record.sudo().write(
                {'x_studio_remaining_quantity': round(record['x_studio_qty_in_hours'] - record['x_studio_consumed_qty'],
                                                      2)})

    def set_project_order_line(self):
        pass

    def _timesheet_service_generation(self):
        pass

    def timesheet_service_generation_ksc(self):
        """ Generates or links tasks/projects for service sale order lines based on service tracking settings.
Prevents duplicate project/task creation when a sale order is reconfirmed.
Reuses existing projects or global projects when applicable.
        """
        so_line_task_global_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_global_project')
        so_line_new_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking in ['project_only', 'task_in_project', 'no'])

        # search so lines from SO of current so lines having their project generated, in order to check if the current one can
        # create its own project, or reuse the one of its order.
        map_so_project = {}
        if so_line_new_project:
            order_ids = self.mapped('order_id').ids
            so_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), (
                'product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                                                 ('product_id.project_template_id', '=', False)])
            map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}
            so_lines_with_project_templates = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), (
                'product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                                                           ('product_id.project_template_id', '!=', False)])
            map_so_project_templates = {(sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id for sol
                                        in so_lines_with_project_templates}

        # search the global project of current SO lines, in which create their task
        map_sol_project = {}
        if so_line_task_global_project:
            map_sol_project = {sol.id: sol.product_id.with_company(sol.company_id).project_id for sol in
                               so_line_task_global_project}

        def _can_create_project(sol):
            """If the sale order line already has a linked project (sol.project_id),
          a new project should NOT be created.
        - If the product has a project template assigned, creation is allowed
          only if the (sale order, template) pair is not already processed
          and not present in `map_so_project_templates`.
        - If the product does not have a template, creation is allowed only
          if the sale order ID is not already included in `map_so_project`."""
            if not sol.project_id:
                if sol.product_id.project_template_id:
                    return (sol.order_id.id, sol.product_id.project_template_id.id) not in map_so_project_templates
                elif sol.order_id.id not in map_so_project:
                    return True
            return False

        def _determine_project(so_line):
            """Determine the project for this sale order line.
            Rules are different based on the service_tracking:

            - 'project_only': the project_id can only come from the sale order line itself
            - 'task_in_project': the project_id comes from the sale order line only if no project_id was configured
              on the parent sale order"""

            if so_line.product_id.service_tracking == 'project_only':
                return so_line.project_id
            elif so_line.product_id.service_tracking == 'task_in_project':
                return so_line.order_id.project_id or so_line.project_id

            return False

        # task_global_project: create task in global project
        for so_line in so_line_task_global_project:
            if not so_line.task_id:
                if map_sol_project.get(so_line.id):
                    so_line._timesheet_create_task(project=map_sol_project[so_line.id])

        # project_only, task_in_project: create a new project, based or not on a template (1 per SO). May be create a task too.
        # if 'task_in_project' and project_id configured on SO, use that one instead
        for so_line in so_line_new_project:
            project = _determine_project(so_line)
            if not project and _can_create_project(so_line):
                project = so_line._timesheet_create_project()
                if so_line.product_id.project_template_id:
                    map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)] = project
                else:
                    map_so_project[so_line.order_id.id] = project
                # INVOICE CREATION
                # self.order_id.auto_invoice_confirm()

            elif not project:
                # Attach subsequent SO lines to the created project
                so_line.project_id = (
                        map_so_project_templates.get((so_line.order_id.id, so_line.product_id.project_template_id.id))
                        or map_so_project.get(so_line.order_id.id)
                )
            if so_line.product_id.service_tracking == 'task_in_project':
                if not project:
                    if so_line.product_id.project_template_id:
                        project = map_so_project_templates[
                            (so_line.order_id.id, so_line.product_id.project_template_id.id)]
                    else:
                        project = map_so_project[so_line.order_id.id]
                if not so_line.task_id:
                    so_line._timesheet_create_task(project=project)


    def _timesheet_link_project(self, project_id):
        """ Generate project for the given so line, and link it.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        self.ensure_one()
        if project_id:
            self.write({'project_id': project_id.id})
        return project_id

    @api.constrains('price_unit')
    def _check_minimum_sale_price(self):
        """- Users who belong to the group
          'ksc_sale_project_extended.group_allow_product_minimum_sale_price'
          are exempt from this validation.
        - For each sale order line:
            * Compute the effective unit price by applying the discount (if any).
            * Compare the effective price with the product's `minimumSalePrice`.
            * If the effective price is lower, block the operation and raise a ValidationError."""
        if not self.env.user.has_group(
                'ksc_sale_project_extended.group_allow_product_minimum_sale_price'):
            for record in self:
                unit_price = record.price_unit
                if record.discount:
                    unit_price -= (unit_price * record.discount) / 100
                if unit_price < record.product_id.minimumSalePrice:
                    raise ValidationError(
                        "The unit price of '%s' must be >= %d%s" % (
                            record.product_id.name, record.product_id.minimumSalePrice,
                            record.product_id.currency_id.symbol))

#
# class SaleOrderOption(models.Model):
#     _inherit = 'sale.order.option'
#
#     @api.constrains('price_unit')
#     def _check_minimum_sale_price_on_opetion(self):
#         if not self.env.user.has_group(
#                 'ksc_sale_project_extended.group_allow_product_minimum_sale_price'):
#             for record in self:
#                 unit_price = record.price_unit
#                 if record.discount:
#                     unit_price -= (unit_price * record.discount) / 100
#                 if unit_price < record.product_id.minimumSalePrice:
#                     raise ValidationError(
#                         "The unit price of '%s' must be >= %d%s" % (
#                             record.product_id.name, record.product_id.minimumSalePrice,
#                             record.product_id.currency_id.symbol))
