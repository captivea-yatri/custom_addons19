# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta,datetime
from dateutil.relativedelta import relativedelta

_TEL_CHARS_TO_REMOVE = [' ', '.', '/', '-']


class Partner(models.Model):
    _inherit = 'res.partner'

    # ########### MIGRATED FIELDS FROM FRANCE ###############
    cap_has_left_company = fields.Boolean(string='Has left company', default=False)
    cap_activity_date_deadline = fields.Date(string='Date dernière activité', related='activity_date_deadline',
                                             store=True)
    cap_phone = fields.Char(string='Téléphone (sans espaces)', compute='compute_clean_phones', store=True)
    cap_mobile = fields.Char(string='Mobile (sans espaces)', compute='compute_clean_phones', store=True)

    # ########### Change that affect automatic customer status ##########
    status = fields.Selection([('not_customer', 'Not a customer'), ('in_progress', 'In Progress'), ('customer', 'Customer'),
                               ('old_customer', 'Old Customer')],
                              string='Status', store=True, compute='_compute_customer_status', index=True)
    customer_since_date = fields.Date("Customer since")
    no_customer_since = fields.Date('Not a customer anymore since')
    solution = fields.Selection([("oe_with_us", "Odoo Enterprise with us"),
                                 ("oe_with_other_partner", "Odoo enterprise with an other partner"),
                                 ("odoo_community", "Odoo Community / One App Free"), ("sugarcrm", "SugarCRM"),
                                 ("cegid", "Cegid XRP Flex"), ("acumatica", "Acumatica")], string='Solution')
    project_ids = fields.One2many('project.project', 'partner_id')
    project_status_id = fields.Many2one('project.status', string='Project State',
                                        compute='_get_current_project_status_id', store=True, compute_sudo=True )
    code = fields.Char(string="Code", related="project_status_id.code")
    enterprise_key = fields.Char('Odoo enterprise key')

    # ########## Changes related to remaining hours and quotation date #################
    remaining_hours = fields.Float('Remaining Hours', compute='_remaining_hours', recursive=True, store=True)
    quotation_sent_date = fields.Date('Latest Quotation sent on', compute='_remaining_hours', store=True)

    property_company_bank_account_id = fields.Many2one('res.partner.bank', 'Company Bank Account',
                                                       company_dependent=True)

    x_studio_authorize_to_log_hours_with_late_invoice = fields.Boolean('Authorize to log hours with late invoice')
    x_studio_authorize_late_amount = fields.Float('Authorize late amount')
    x_studio_authorize_late_until = fields.Date('Authorize late until')
    late_invoice_status = fields.Text('Late Invoice Status', compute='compute_late_invoice_status')

    x_studio_sales_status = fields.Selection([('Active Payment in Advance', 'Active Payment in Advance'),
                                              ('Active Pay as you go', 'Active Pay as you go'),
                                              ('Inactive', 'Inactive')], string='Sales Status')

    customer_satisfaction = fields.Selection([('0', 'Normal'), ('1', 'Low'), ('2', 'Medium'), ('3', 'High'),
                                              ('4', 'Very High')], string="Customer Satisfaction", tracking=True)
    last_customer_satisfaction_update = fields.Date(string='Last Customer Satisfaction Update')
    agree_to_recommend_us = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Agree To Recommend Us',
                                             tracking=True)
    last_agree_to_recommend_us = fields.Date(string='Last Agree to Recommend us')
    communicate_contact_to_our_lead = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                                       string='We Can Communicate This Contact To Our Lead',
                                                       tracking=True)
    last_communicate_contact_to_our_lead_update = fields.Date(string='Last Communicate Contact To Our Lead Update')
    contact_information_to_communicate_to_our_lead = fields.Text(string='Contact Info To Communicate To Our Lead')
    status_of_testimonial = fields.Text(string='Status Of Testimonial')
    status_of_both_way_communication = fields.Text(string='Status Of Both Way Communication')
    job_position_for_marketing = fields.Selection(
        [('ceo_president', 'CEO / President'), ('chief_finance_accointing', 'Chief Finance / Accounting'),
         ('other_finance_function', 'Other Finance function'), ('chief_operation', 'Chief Operation'),
         ('other_operation_function', 'Other Operation function'),
         ('chief_information_system', 'Chief Information System'),
         ('other_information_system_function', 'Other Information System function'),
         ('chief_revenue_sales', 'Chief Revenue / Sales'), ('other_sales_function', 'Other Sales function'),
         ('chief_marketing', 'Chief Marketing'), ('other_marketing_function', 'Other Marketing function'),
         ('chief_human_resources', 'Chief Human Resources'),
         ('other_human_resource_function', 'Other Human Resources function'), ('other', 'Other')])
    project_count = fields.Integer(string='Project Count', compute='_compute_project_count')
    x_studio_customer_of = fields.Many2one(string='Customer of', comodel_name='res.company', readonly=True)
    user_id = fields.Many2one('res.users', string='Salesperson',
                              help='The internal user in charge of this contact.', compute='_compute_user_id',
                              store=True, inverse='_inverse_user_id', default=lambda self: self.env.user.id)

    ################## Manage Customer's status - Cron optimization ###################
    all_child_ids = fields.Many2many(
        'res.partner',
        'res_partner_all_child_rel',
        'partner_id',
        'child_id',
        string='All Child Contacts',
        compute='_compute_all_child_ids',
        store=False,
    )

    def _included_unreconciled_aml_max_followup(self):
        """ Computes the maximum delay in days and the highest level of followup (followup line with highest delay) of all the unreconciled amls included.
        Also returns the delay for the next level (after the highest_followup_line), the most delayed aml and a boolean specifying if any invoice is overdue.
        :return dict with key/values: most_delayed_aml, max_delay, highest_followup_line, next_followup_delay, has_overdue_invoices
        """
        """This method is defined while migrating to version 19 due to in V19 method is deprecated from base """
        """It is being use to bring data related to late journal items"""
        self.ensure_one()
        today = fields.Date.context_today(self)
        highest_followup_line = None
        most_delayed_aml = self.env['account.move.line']
        first_followup_line = self._get_first_followup_level()
        # Minimum value for delay, will always be smaller than any other delay
        max_delay = first_followup_line.delay - 1
        has_overdue_invoices = False
        for aml in self.unreconciled_aml_ids.filtered('date_maturity'):
            aml_delay = (today - aml.date_maturity).days

            is_overdue = aml_delay > 0
            if is_overdue:
                has_overdue_invoices = True

            if self.env.company in aml.company_id.parent_ids:
                if aml.followup_line_id and aml.followup_line_id.delay >= (
                        highest_followup_line or first_followup_line).delay:
                    highest_followup_line = aml.followup_line_id
                max_delay = max(max_delay, aml_delay)
                if most_delayed_aml.amount_residual < aml.amount_residual:
                    most_delayed_aml = aml
        followup_lines_info = self._get_followup_lines_info()
        next_followup_delay = None
        if followup_lines_info:
            key = highest_followup_line.id if highest_followup_line else None
            current_followup_line_info = followup_lines_info.get(key)
            next_followup_delay = current_followup_line_info.get('next_delay')
        return {
            'most_delayed_aml': most_delayed_aml,
            'max_delay': max_delay,
            'highest_followup_line': highest_followup_line,
            'next_followup_delay': next_followup_delay,
            'has_overdue_invoices': has_overdue_invoices,
        }

    @api.depends('child_ids', 'child_ids.child_ids')
    def _compute_all_child_ids(self):
        """Compute all recursive child partners and store them in all_child_ids."""
        for partner in self:
            all_children = partner._get_all_children_recursive()
            partner.all_child_ids = [(6, 0, all_children.ids)]

    def _get_all_children_recursive(self):
        """Recursive lookup of all child partners."""
        self.ensure_one()
        visited = self.env['res.partner'].browse()
        to_process = self.child_ids
        while to_process:
            child = to_process[0]
            to_process = to_process[1:]
            if child not in visited:
                visited += child
                to_process += child.child_ids
        return visited

    @api.onchange('parent_id')
    @api.depends('user_id', 'opportunity_ids.user_id',)
    def _compute_user_id(self):
        """Compute salesperson based on latest opportunity from partner or its children."""
        if not self.env.context.get('from_server', False):
            partner_company = self.env['res.company'].search([('partner_id', '!=', False)]).mapped('partner_id')
            for rec in self:
                if rec.id in partner_company.ids or rec.parent_id.id in partner_company.ids or rec._origin.id in partner_company.ids or rec.parent_id._origin.id in partner_company.ids:
                    continue
                elif rec.is_company == True:
                    opportunity_ids = rec.opportunity_ids + rec.child_ids.opportunity_ids
                    sorted_opportunity_ids = opportunity_ids.sorted('create_date')
                    if sorted_opportunity_ids and sorted_opportunity_ids[-1].user_id:
                        rec.user_id = sorted_opportunity_ids[-1].user_id
                    all_child_ids = rec.search([('id', 'child_of', self.ids)])
                    for child_id in all_child_ids:
                        child_id.user_id = rec.user_id
                elif rec.parent_id:
                    opportunity_ids = rec.opportunity_ids + rec.parent_id.opportunity_ids
                    sorted_opportunity_ids = opportunity_ids.sorted('create_date')
                    if sorted_opportunity_ids and sorted_opportunity_ids[-1].user_id:
                        rec.parent_id.user_id = sorted_opportunity_ids[-1].user_id
                        all_child_ids = rec.search([('id', 'child_of', rec.parent_id.ids)])
                        for child_id in all_child_ids:
                            child_id.user_id = rec.parent_id.user_id
                else:
                    opportunity_ids = rec.opportunity_ids
                    sorted_opportunity_ids = opportunity_ids.sorted('create_date')
                    if sorted_opportunity_ids and sorted_opportunity_ids[-1].user_id:
                        rec.user_id = sorted_opportunity_ids[-1].user_id

    def _inverse_user_id(self):
        """Propagate salesperson to all child partners when modified on a company partner."""
        for rec in self:
            if rec.is_company == True:
                all_child_ids = rec.search([('id', 'child_of', self.ids)])
                for child_id in all_child_ids:
                    child_id.user_id = rec.user_id

    @api.model
    def _commercial_fields(self):
        # 'status', 'customer_since_date', 'no_customer_since', 'x_studio_sales_status', 'project_status_id'
        """Extend commercial fields to include custom customer-related properties."""
        return super(Partner, self)._commercial_fields() + \
            ['solution',
             'enterprise_key', 'customer_satisfaction', 'agree_to_recommend_us', 'last_customer_satisfaction_update',
             'communicate_contact_to_our_lead', 'last_communicate_contact_to_our_lead_update',
             'contact_information_to_communicate_to_our_lead', 'status_of_testimonial',
             'status_of_both_way_communication', 'last_agree_to_recommend_us']

    def get_followup_status_with_x_studio_customer_of(self):
        """
        This function gets followup status based on field x_studio_customer_of.
        """
        today = fields.Date.context_today(self)
        followup_lines_info = self.with_company(self.x_studio_customer_of)._get_followup_lines_info()
        max_followup = self.with_company(self.x_studio_customer_of)._included_unreconciled_aml_max_followup()
        max_aml_delay = max_followup.get('max_delay') or 0
        next_followup_delay = max_followup.get('next_followup_delay') or 0
        has_overdue_invoices = max_followup.get('has_overdue_invoices')
        most_delayed_aml = max_followup.get('most_delayed_aml')

        # computation of followup_status
        followup_status = 'no_action_needed'
        if has_overdue_invoices and most_delayed_aml:
            followup_status = 'with_overdue_invoices'
        next_followup_date_exceeded = today >= self.with_company(self.x_studio_customer_of).followup_next_action_date \
            if self.with_company(self.x_studio_customer_of).followup_next_action_date else True
        if max_aml_delay > next_followup_delay and next_followup_date_exceeded and followup_lines_info:
            followup_status = 'in_need_of_action'
        return followup_status

    def compute_late_invoice_status(self):
        """
        This function set the late invoice status on contact.
        """
        for rec in self.filtered(lambda rec: rec.x_studio_customer_of != False):
            followup_status = rec.sudo().get_followup_status_with_x_studio_customer_of()
            not_paid_invoice_ids = rec.sudo().invoice_ids.filtered(
                lambda move: move.state == 'posted' and move.move_type == 'out_invoice' and
                             move.payment_state in ['not_paid', 'partial'] and move.invoice_date_due != False and
                             move.invoice_date_due < fields.Date.today() and
                             move.company_id.id == rec.x_studio_customer_of.id)
            if rec.x_studio_authorize_to_log_hours_with_late_invoice == True:
                rec.late_invoice_status = str(rec.name) + " is unblocked till '" + \
                                          str(rec.x_studio_authorize_late_until) + "' for '" + \
                                          rec.currency_id.symbol + " " + str(round(rec.x_studio_authorize_late_amount, 2)) + \
                                          "' in late."
            elif followup_status not in ['in_need_of_action', 'with_overdue_invoices'] and not not_paid_invoice_ids:
                rec.late_invoice_status = str(rec.name) + " is on-time."
            elif followup_status in ['in_need_of_action', 'with_overdue_invoices'] and not_paid_invoice_ids \
                and min(not_paid_invoice_ids.mapped('invoice_date_due')) + timedelta(
                    days=rec.x_studio_customer_of.number_of_days_authorized_in_late) >= fields.Date.today():
                rec.late_invoice_status = str(rec.name) + " is in-late, it will be locked soon."
            else:
                rec.late_invoice_status = str(rec.name) + " is Blocked."

    @api.depends('child_ids.remaining_hours', 'sale_order_ids.state',
                 'sale_order_ids.quotation_sent_date', 'sale_order_ids.order_line.x_studio_remaining_quantity')
    def _remaining_hours(self):
        """Compute total remaining prepaid service hours and latest quotation sent date."""
        for rec in self:
            all_child_ids = rec.search([('id', 'child_of', rec.ids)])
            sale_order_ids = self.env['sale.order'].search([('partner_id', 'in', all_child_ids.ids),
                                                            ('state', 'in', ['sale', 'done'])])
            rec.remaining_hours = sum(
                line.x_studio_remaining_quantity for order in sale_order_ids
                for line in order.order_line.filtered(lambda l: l.product_id.type == 'service' and
                                                                l.product_id.service_policy == 'ordered_prepaid'))
            sale_order_id = self.env['sale.order'].search([('partner_id', 'in', all_child_ids.ids),
                                                            ('quotation_sent_date', '!=', False)],
                                                          order='quotation_sent_date DESC').filtered(lambda so: so.state == 'sent')
            rec.quotation_sent_date = sale_order_id and sale_order_id[-1].quotation_sent_date or ''

########################################## Manage customer's status - UPDATED ################################################

    @api.depends('sale_order_ids', 'sale_order_ids.state', 'opportunity_ids', 'opportunity_ids.stage_id',
                 'opportunity_ids.active', 'x_studio_sales_status')
    def _compute_customer_status(self):
        """Compute customer lifecycle status (customer, old, in progress, etc.) based on orders and opportunities based on various parameters related to sale orders and invoices."""
        if not self.env.context.get('not_execute_customer_status', False):
            for rec in self:
                partner_id = rec._get_parent_id()
                partner_id = partner_id._origin  # Use original object for parent partner
                # Fetch all sale orders and opportunities in one go, and filter once
                sale_order_ids = self.env['sale.order'].search([('partner_id', 'child_of', partner_id.id)])
                opportunity_ids = partner_id.opportunity_ids + partner_id.all_child_ids.opportunity_ids
                status = ''
                x_studio_sales_status = partner_id.x_studio_sales_status or False
                customer_since_date = partner_id.customer_since_date or None
                no_customer_since = None
                today = fields.Date.today()
                one_year_before = today + relativedelta(days=-365)

                if sale_order_ids and any(sale.state in ['sale', 'done'] for sale in sale_order_ids):
                    sale_order_ids = sale_order_ids.filtered(lambda so: so.state in ['sale', 'done']).sorted('date_order',
                                                                                                             reverse=True)
                    latest_sale = sale_order_ids[0]
                    timesheet_id = self.env['account.analytic.line'].search([
                        ('name', '!=', 'Closing of the SO'),
                        ('project_id.active', '!=', False),
                        ('task_id.active', '!=', False),
                        ('date', '>', one_year_before),
                        '|',
                        ('partner_id', '=', partner_id.id),
                        ('partner_id', 'in', partner_id.all_child_ids.ids)
                    ], order='date desc', limit=1)
                    if latest_sale.date_order.date() > today + relativedelta(days=-120):
                        based_on_timesheet_product = latest_sale.order_line.filtered(
                            lambda line: line.product_id.service_policy == 'delivered_timesheet')
                        x_studio_sales_status = 'Active Pay as you go' if based_on_timesheet_product else 'Active Payment in Advance'
                        status = 'customer'
                        if not partner_id.customer_since_date:
                            date_order = latest_sale.date_order
                            customer_since_date = date_order
                            # Code Commented by Jaykishan
                            # if partner_id.user_id:
                            #     partner_id.create_activity_to_fill_customer_info()
                    elif latest_sale.date_order.date() > one_year_before:
                        x_studio_sales_status = 'Inactive'
                        status = 'customer'
                        if not partner_id.customer_since_date:
                            date_order = latest_sale.date_order
                            customer_since_date = date_order
                            # Code Commented by Jaykishan
                            # if partner_id.user_id:
                            #     partner_id.create_activity_to_fill_customer_info()
                    elif not timesheet_id:
                        status = 'old_customer'
                        x_studio_sales_status = 'Inactive'
                    else:
                        status = 'customer'
                        x_studio_sales_status = 'Inactive'
                elif sale_order_ids and any(
                        sale.state == 'cancel' for sale in sale_order_ids) and partner_id.customer_since_date:
                    status = 'old_customer'
                    x_studio_sales_status = 'Inactive'
                    no_customer_since = today
                elif opportunity_ids and all(opportunity_id.active is False for opportunity_id in opportunity_ids):
                    status = 'not_customer'
                elif opportunity_ids and opportunity_ids.filtered(
                        lambda opp: opp.active and not opp.stage_id.is_won) or opportunity_ids.filtered(
                        lambda opp: opp.active and opp.stage_id.is_won and not sale_order_ids):
                    status = 'in_progress'
                else:
                    status = 'not_customer'
                partner_id.with_context(update_status=True)._set_customer_status_child(status, customer_since_date,
                                                                                   no_customer_since, x_studio_sales_status,
                                                                                   False)

    def _set_customer_status_child(self, status, customer_since_date, no_customer_since, x_studio_sales_status,
                                   project_status_id):
        """Applying computed customer status to the partner and all its descendants."""
        if not self:
            return

        all_partners = self | self.all_child_ids  # Combine parent + children

        # Update only with context (not from _get_current_project_status_id)
        if self.env.context.get('update_status', False):
            update_vals = {
                'status': status,
                'customer_since_date': customer_since_date,
                'no_customer_since': no_customer_since,
            }
            if x_studio_sales_status:
                update_vals['x_studio_sales_status'] = x_studio_sales_status
            # Batch write
            all_partners.with_context(not_execute_customer_status=True).write(update_vals)

        if self.env.context.get('update_project_status', False) and project_status_id:
            # Sudoed batch write
            all_partners.sudo().write({'project_status_id': project_status_id})

    def _get_parent_id(self):
        """Return the root parent partner (top of the hierarchy)."""
        # Start with the current record
        current = self
        # Iterate while there is a parent_id
        while current.parent_id:
            current = current.parent_id  # Move up the parent chain
        return current

########################################################################################################################

    @api.depends('project_ids', 'project_ids.project_status_id')
    def _get_current_project_status_id(self):
        """
        Computes the project status based on latest project linked to the partner.
        """
        for rec in self._origin:
            rec = rec._get_parent_id()
            project_ids = self.env['project.project'].search([('partner_id', 'child_of', rec.id)])
            sorted_projects = project_ids.sorted(lambda x: x.create_date)
            project_state = False
            if project_ids:
                project_state = sorted_projects[-1].project_status_id
                rec.sudo().write({'project_status_id': project_state.id})
            else:
                rec.sudo().project_status_id = False
            rec.with_context(update_project_status=True)._set_customer_status_child(False, False, False, False, project_state)

    @api.depends('phone', 'phone_mobile_search')
    def compute_clean_phones(self):
        """Clean phone and mobile fields by removing spaces and formatting characters."""

        for record in self:
            if record.phone:
                record.cap_phone = "".join([c for c in record.phone if c not in _TEL_CHARS_TO_REMOVE])
            else:
                record.cap_phone = False

            if record.phone_mobile_search:
                record.cap_mobile = "".join([c for c in record.phone_mobile_search if c not in _TEL_CHARS_TO_REMOVE])
            else:
                record.cap_mobile = False

    def _compute_project_count(self):
        """Compute total number of projects linked to the partner and its hierarchy."""
        for partner in self:
            all_partners = self.with_context(active_test=False).search([('id', 'child_of', partner.ids)])
            partner.project_count = self.env['project.project'].search_count([('partner_id', 'in', all_partners.ids)])

    def action_view_projects(self):
        """Open the project list view filtered by partner and all its child contacts."""
        action = self.env['ir.actions.act_window']._for_xml_id('cap_partner.act_project_project_views')
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action
