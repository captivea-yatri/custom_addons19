from odoo import models, fields, api, modules
from collections import defaultdict


class ResUsers(models.Model):
    _inherit = "res.users"

    parent_ids = fields.Many2many('res.users', 'rel_res_users_res_users', 'parent_id', 'child_id',
                                  compute='_compute_parent_ids', store=True)

    @api.depends('employee_ids', 'employee_ids.parent_id')
    def _compute_parent_ids(self):
        for rec in self:
            emp_ids = self.env['hr.employee'].search([('user_id', '=', rec.id)])
            if emp_ids:
                for emp_id in emp_ids:
                    child_emp_ids = self.env['hr.employee'].search([('id', 'child_of', emp_id.ids)])
                    for child_emp_id in child_emp_ids:
                        child_emp_id.set_parent_ids(child_emp_id.user_id)
                    emp_id.set_parent_ids(rec)
            else:
                rec.parent_ids = False

    def link_partners(self):
        users = self.search([])
        users = users.filtered(lambda rec: rec.has_group('base.group_user') and rec.id != self.id)
        self.partner_id.accessible_user_ids = [(4, u.id) for u in users]
        for rec in users:
            rec.partner_id.accessible_user_ids = [(4, self.id)]

    @api.model
    def systray_get_activities(self):
        """
        Override this method to display activities which are created on archived leads.
        """
        activities = self.env["mail.activity"].search([("user_id", "=", self.env.uid)])
        activities_by_record_by_model_name = defaultdict(lambda: defaultdict(lambda: self.env["mail.activity"]))
        for activity in activities:
            record = self.env[activity.res_model].browse(activity.res_id)
            activities_by_record_by_model_name[activity.res_model][record] += activity
        model_ids = list({self.env["ir.model"]._get(name).id for name in activities_by_record_by_model_name.keys()})
        user_activities = {}
        for model_name, activities_by_record in activities_by_record_by_model_name.items():
            domain = [("id", "in", list({r.id for r in activities_by_record.keys()}))]
            if model_name == 'crm.lead':
                domain += ['|', ('active', '=', True), ('active', '=', False)]
                allowed_records = self.env[model_name].search(domain)
                if not allowed_records:
                    continue
            else:
                allowed_records = self.env[model_name].search(domain)
                if not allowed_records:
                    continue
            module = self.env[model_name]._original_module
            icon = module and modules.module.get_module_icon(module)
            model = self.env["ir.model"]._get(model_name).with_prefetch(model_ids)
            user_activities[model_name] = {
                "id": model.id,
                "name": model.name,
                "model": model_name,
                "type": "activity",
                "icon": icon,
                "total_count": 0,
                "today_count": 0,
                "overdue_count": 0,
                "planned_count": 0,
                "actions": [
                    {
                        "icon": "fa-clock-o",
                        "name": "Summary",
                    }
                ],
            }
            for record, activities in activities_by_record.items():
                if record not in allowed_records:
                    continue
                for activity in activities:
                    user_activities[model_name]["%s_count" % activity.state] += 1
                    if activity.state in ("today", "overdue"):
                        user_activities[model_name]["total_count"] += 1
        return list(user_activities.values())

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResUsers, self).create(vals_list)
        if 'employee_ids' in vals_list:
            self.calculate_employee()
        return res

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if 'employee_ids' in vals:
            self.calculate_employee()
        return res

    def calculate_employee(self):
        """
        Recalculate the employee.
        Assign the employee associated with the same company as the user.
        """
        for rec in self:
            for emp in rec.employee_ids.filtered(lambda emp: emp.active and emp.company_id.id == rec.company_id.id):
                rec.x_studio_employee = emp.id
