from odoo import models, api
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def set_parent_ids(self, user_id):
        user_id.sudo().parent_ids = [(4, self.user_id.id)]
        if self.parent_id and self.parent_id.user_id and self.parent_id.id != self.id:
            self.parent_id.set_parent_ids(user_id)

    def remove_parent_ids(self, user_id):
        user_id.sudo().parent_ids = [(3, self.user_id.id)]
        if self.parent_id and self.parent_id.user_id and self.parent_id.id != self.id:
            self.parent_id.remove_parent_ids(user_id)

    # def get_managers_recursive(self, manager_ids):
    #     if manager_ids is None:
    #         manager_ids = []
    #     if self.parent_id:
    #         if self.parent_id.user_id and self.parent_id.user_id.id not in manager_ids:
    #             manager_ids.append(self.parent_id.user_id.id)
    #         self.parent_id.get_managers_recursive(manager_ids)
    #     return manager_ids

# TO stop the recusrive error in odoo 19 db
    def get_managers_recursive(self, manager_ids=None):
        """
        Collect all manager user_ids up the hierarchy safely.

        Prevents cyclic relationships and avoids multi-company access errors.
        """

        if manager_ids is None:
            manager_ids = []

        visited = set()

        # use sudo to avoid multi-company employee rule
        current = self.sudo().parent_id

        while current:

            if current.id in visited:
                raise UserError(
                    "Cyclic manager hierarchy detected. "
                    "Please correct the reporting structure."
                )

            visited.add(current.id)

            # add manager's user
            if current.user_id and current.user_id.id not in manager_ids:
                manager_ids.append(current.user_id.id)

            # move up hierarchy safely
            current = current.sudo().parent_id

        return manager_ids

    def write(self, vals):
        """
        This method creates an access request when we change an employee's manager.
        """
        for rec in self:
            if 'parent_id' in vals and vals.get('parent_id') != rec.parent_id.id:
                rec.remove_parent_ids(rec.user_id)
                child_emp_ids = self.env['hr.employee'].search([('id', 'child_of', self.ids)])
                for child_emp_id in child_emp_ids.filtered(lambda child_emp_id: child_emp_id.user_id):
                    child_emp_id.remove_parent_ids(child_emp_id.user_id)
            if 'active' in vals and vals.get('active') == False:
                vals.update({'parent_id': False})
        res = super(HrEmployee, self).write(vals)
        for record in self:
            if vals.get('parent_id'):
                if record.parent_id.child_ids and record.parent_id.user_id:
                    for role in record.parent_id.user_id.role_line_ids.filtered(
                            # lambda role: role.role_id.id in [
                            #     self.env.ref('access_rights_management.role_team_manager_data').id,
                            #     self.env.ref('access_rights_management.role_team_director_data').id
                            # ]):
                            lambda role: role.role_id.id in [
                                self.env.ref('base.group_user').id,
                            ]):
                        emp_request_ids = self.env['emp.access.request'].search([
                            ('state', '=', 'Approved'),
                            ('employee_id', '=', record.id)
                        ])
                        partner_ids = emp_request_ids.mapped('partner_id')
                        existing_request_ids = self.env['emp.access.request'].search([
                            ('partner_id', 'in', partner_ids.ids),
                            ('employee_id', '=', record.parent_id.id),
                        ])
                        partners_without_request_ids = partner_ids - existing_request_ids.mapped('partner_id')
                        for partner_id in partners_without_request_ids:
                            emp_access_request_ids = self.env['emp.access.request'].with_context(
                                auto_emp_access_req_approve=True).sudo().create({
                                'partner_id': partner_id.id,
                                'employee_id': record.parent_id.id,
                                'manager_user_id': record.parent_id.parent_id.user_id.id,
                            })
                            emp_access_request_ids.sudo().button_approved()
        return res

