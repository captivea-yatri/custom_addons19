from odoo import api, models, fields, _


class Task(models.Model):
    _inherit = "project.task"

    @api.model_create_multi
    def create(self, vals_list):
        """
            Overrides task creation to ensure assigned users have access to the
            project's customer. Automatically triggers access request creation
            for users who do not already have customer access.
            """
        res = super(Task, self).create(vals_list)
        for rec in res:
            if rec.project_id.partner_id and rec.user_ids:
                rec.create_access_for_user_if_task(rec.user_ids)
        return res

    def write(self, vals):
        """
           Overrides task update to detect newly assigned users. If new users
           are added to the task, the system verifies their access to the
           project customer and generates access requests when required.
           """
        old_user_map = {rec.id: rec.user_ids.ids for rec in self}
        res = super(Task, self).write(vals)
        for rec in self:
            if 'user_ids' in vals and rec.project_id.partner_id:
                old_user_ids = set(old_user_map.get(rec.id, []))
                new_user_ids = set(rec.user_ids.ids)
                added_users = new_user_ids - old_user_ids
                if added_users != {}:
                    added_user_records = self.env['res.users'].browse(list(added_users))
                    rec.create_access_for_user_if_task(added_user_records)
        return res

    def create_access_for_user_if_task(self, users):
        """
            The method checks the user's employee record and recursively
            evaluates the managerial hierarchy, generating access requests
            where necessary until an authorized user is found.
            """
        for rec in self:
            if not rec.project_id.partner_id:
                continue
            partner = (rec.project_id.partner_id.parent_id or rec.project_id.partner_id).sudo()
            for user in users:
                # if (user.has_group(
                #         'access_rights_management.role_operation') or user.has_group(
                #     'access_rights_management.role_operation_on_boarder') or user.has_group(
                #     'access_rights_management.role_team_manager') or user.has_group(
                #     'access_rights_management.role_team_director')):
                if not user.has_group('base.group_user'):
                    continue
                # FIX: search employee with sudo
                employee = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', user.id)], limit=1
                )
                if not employee:
                    continue
                current_employee = employee
                while current_employee:
                    user_rec = current_employee.user_id
                    if not user_rec:
                        break
                    if user_rec.id in partner.accessible_user_ids.ids:
                        break
                    existing_req = self.env['emp.access.request'].sudo().search_count([
                        ('partner_id', '=', partner.id),
                        ('state', 'in', ['Approved', 'Requested', 'Renewal']),
                        ('employee_id', '=', current_employee.id)
                    ])
                    if not existing_req:
                        self.env['emp.access.request'].sudo().create({
                            'partner_id': partner.id,
                            'state': 'Requested',
                            'employee_id': current_employee.id,
                            'manager_user_id': current_employee.parent_id.user_id.id
                            if current_employee.parent_id and current_employee.parent_id.user_id else False
                        })
                    current_employee = current_employee.parent_id

