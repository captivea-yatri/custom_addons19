from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Contact'

    accessible_user_ids = fields.Many2many('res.users', 'rel_res_partner_res_users', 'partner_id',
                                           'accessible_user_id', 'Accessible User')
    is_access = fields.Boolean('Is Access', compute='_compute_is_access')

    def _compute_is_access(self):
        for rec in self:
            if self.env.user.id in rec.accessible_user_ids.ids:
                rec.is_access = True
            else:
                rec.is_access = False

    def view_access_req(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("ksc_emp_customer_access.my_rec_access_action")
        all_child = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        action['domain'] = [('partner_id', 'in', all_child.ids), '|', ('employee_id.user_id', '=', self.env.uid),
                            ('manager_user_id', '=', self.env.uid)]
        action['context'] = {'default_state': 'Requested',
                             'active_test': False,
                             'default_partner_id': self.id}
        return action

    def action_view_sale_order(self):
        self.ensure_one()
        # if self.env.user.has_groups('access_rights_management.role_team_manager') or self.env.user.has_groups(
        #         'access_rights_management.role_team_director') or self.env.user.has_groups(
        #     'access_rights_management.role_operation') or self.env.user.has_groups(
        #     'access_rights_management.role_operation_on_boarder'):
        if self.env.user.has_groups('base.group_user'):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'name': ('Quotations and Sales'),
                'view_mode': 'list,form',
                'views': [[self.env.ref('sale.view_order_tree').id, 'list'],
                          [self.env.ref('sale.view_order_form').id, 'form']],
                'context': {'default_partner_id': self.id},
                'domain': ['|', ('partner_id', '=', self.id), ('partner_id', 'in', self.child_ids.ids)]
            }
        else:
            return super(ResPartner, self).action_view_sale_order()

    # @api.model_create_multi
    # def create(self, vals_list):
    #     vals_list[0].update({'accessible_user_ids': [(4, self.env.user.id)]})
    #     res = super(ResPartner, self).create(vals_list)
    #     return res

    def write(self, vals):
        """
        here, we check customer's status,
        - if customer's status is customer and the customer is link in field ana_account_partner_ids then we unlink the
          customer from here to manage the expense records for access request based roles.
        - if customer became old_customer then we link the customer in field ana_account_partner_ids.
        - if status changes from non-customer to customer, we create and approve employee access requests.
        """

        partners_to_process = self.env["res.partner"]
        if vals.get("status") == "customer":
            for partner in self:
                if partner.status not in ["customer", "old_customer"]:
                    partners_to_process |= partner

        res = super(ResPartner, self).write(vals)

        companies_partner = self.env['res.company'].search([]).mapped('partner_id')
        for rec in self:
            # if not self.env.user.has_groups('access_rights_management.role_president') and (
            if not self.env.user.has_groups('base.group_system') and (
                    rec.id in companies_partner.ids):
                if not self.env.su:
                    if not (len(vals) == 1 and vals.get('child_ids')) and not (
                            len(vals) == 1 and vals.get('accessible_user_ids')):
                        raise AccessError("Only President can modify this contact")

        # Expense/analytic account linking logic
        if vals.get('status'):
            for rec in self:
                if rec.status == 'customer':
                    expense_ids = rec.env['hr.expense'].search([('ana_account_partner_ids', '=', rec.id)])
                    for expense_id in expense_ids:
                        expense_id.ana_account_partner_ids = [(3, rec.id)]
                elif rec.status != False:
                    analytic_account_ids = rec.env['account.analytic.account'].search([('partner_id', '=', rec.id)])
                    for analytic_account_id in analytic_account_ids:
                        expense = rec.env['hr.expense'].search([('analytic_account_ids', '=', analytic_account_id.id)])
                        expense.ana_account_partner_ids = [(4, rec.id)]

        for partner in partners_to_process:
            sale_order = self.env["sale.order"].search(
                [("partner_id", "=", partner.id)],
                order="date_order desc",
                limit=1
            )
            if not sale_order:
                continue

            partner_to_use = sale_order.partner_id
            if not partner_to_use.is_company and partner_to_use.parent_id:
                partner_to_use = partner_to_use.parent_id

            matching_offer = sale_order.company_id.offer_ids.filtered(
                lambda o: o.offer_id.id == sale_order.offer_id.id
            )
            if not matching_offer:
                continue

            employee_id = matching_offer.user_id.mapped("x_studio_employee")
            if not employee_id:
                continue

            existing_request = self.env["emp.access.request"].search_count([
                ("partner_id", "=", partner_to_use.id),
                ("employee_id", "=", employee_id.id),
            ])
            if existing_request:
                continue

            vals = {
                "partner_id": partner_to_use.id,
                "employee_id": employee_id.id,
            }

            if employee_id.parent_id:
                vals["manager_user_id"] = employee_id.parent_id.user_id.id

            access_request = self.env["emp.access.request"].with_context(auto_emp_access_req_approve = True).create(vals)
            if access_request:
                access_request.button_approved()

        return res
