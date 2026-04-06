from odoo import models, api


class ResUsersLine(models.Model):
    _inherit = "res.users.role.line"

    @api.model_create_multi
    def create(self, vals_list):
        order = super(ResUsersLine, self).create(vals_list)
        order.change_role_id()
        return order

    def write(self, vals):
        res = super(ResUsersLine, self).write(vals)
        self.change_role_id()
        return res

    def change_role_id(self):
        """
        This Methods Work To Create Access Request When Change User Role Accepted Only Team Manager Or Team Director.
        Check User Employee Have Childs Are Not If Employee Have Childs Then Only Create Access Request.
        """
        for record in self:
            employee_ids = self.env['hr.employee'].search([('user_id', '=', record.user_id.id)])

            if employee_ids and record.role_id.id in [
                # self.env.ref('access_rights_management.role_team_manager_data').id,
                # self.env.ref('access_rights_management.role_team_director_data').id]:
                self.env.ref('base.group_user').id]:
                child_user_ids = employee_ids.mapped('child_ids.user_id')
                matching_customers_ids = self.env['res.partner'].search([('accessible_user_ids', 'in', child_user_ids.ids)])

                for employee in employee_ids:
                    emp_request_ids = self.env['emp.access.request'].search([
                        ('state', '=', 'Approved'),
                        ('employee_id', 'in', employee.child_ids.ids)
                    ])
                    partner_ids = emp_request_ids.mapped('partner_id')
                    for partner_id in partner_ids:
                        existing_request_id = self.env['emp.access.request'].search([
                            ('partner_id', '=', partner_id.id),
                            ('employee_id', '=', employee.id),
                            ('state', '=', 'Approved'),
                        ])

                        if not existing_request_id:
                            emp_access_request_ids = self.env['emp.access.request'].with_context(
                                auto_emp_access_req_approve=True).sudo().create({
                                'partner_id': partner_id.id,
                                'employee_id': employee.id,
                                'manager_user_id': record.user_id.employee_parent_id.user_id.id,
                            })
                            emp_access_request_ids.button_approved()
