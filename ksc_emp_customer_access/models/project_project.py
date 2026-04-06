from odoo import api, models, fields, _


class Project(models.Model):
    _inherit = "project.project"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Automatically creates and approves an employee access request when a project
        is created for eligible operational or management users who lack partner access.
        Uses auto-approval context to skip manager involvement and follower assignment.
        """
        res = super(Project, self).create(vals_list)
        for rec in res:
            if rec.partner_id and rec.user_id:
                # if (rec.user_id.has_group(
                #         'access_rights_management.role_operation') or rec.user_id.has_group(
                #     'access_rights_management.role_operation_on_boarder') or rec.user_id.has_group(
                #     'access_rights_management.role_team_manager') or rec.user_id.has_group(
                #     'access_rights_management.role_team_director')):
                if (rec.user_id.has_group('base.group_user')):
                    parent_id = rec.partner_id.parent_id if rec.partner_id.parent_id else rec.partner_id
                    if rec.user_id.id in parent_id.accessible_user_ids.ids:
                        continue
                    else:
                        access_req = self.env['emp.access.request'].with_context(auto_emp_access_req_approve = True).sudo().create({
                            'partner_id': parent_id.id,
                            'state': 'Requested',
                            'employee_id': rec.user_id.x_studio_employee.id,
                            'manager_user_id': rec.user_id.x_studio_employee.parent_id.user_id.id if rec.user_id.x_studio_employee.parent_id.user_id else False
                        })
                        access_req.sudo().button_approved()
        return res

    def write(self, vals):
        """
            If the new user does not have access to the related customer,
            an employee access request is automatically created and approved.
            Prevents creating requests when the customer is removed.
            """
        res = super(Project, self).write(vals)
        for rec in self:
            if vals.get('user_id') or vals.get('partner_id'):
                # Prevent blank request when customer removed
                if not rec.partner_id:
                    continue
                # FIX: ensure user exists
                if rec.user_id and rec.user_id.has_group('base.group_user'):
                    parent_id = rec.partner_id.parent_id if rec.partner_id.parent_id else rec.partner_id
                    if rec.user_id.id in parent_id.accessible_user_ids.ids:
                        continue
                    access_req = self.env['emp.access.request'].with_context(
                        auto_emp_access_req_approve=True
                    ).sudo().create({
                        'partner_id': parent_id.id,
                        'state': 'Requested',
                        'employee_id': rec.user_id.x_studio_employee.id,
                        'manager_user_id': rec.user_id.x_studio_employee.parent_id.user_id.id
                        if rec.user_id.x_studio_employee.parent_id.user_id else False
                    })
                    access_req.sudo().button_approved()
        return res

