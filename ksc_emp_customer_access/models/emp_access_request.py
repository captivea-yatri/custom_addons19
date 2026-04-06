from datetime import date
from odoo.exceptions import UserError
from odoo import models, api, fields
from dateutil.relativedelta import relativedelta

class EmpAccessRequest(models.Model):
    _name = "emp.access.request"
    _description = "Employee Access Request"
    _rec_name = "partner_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'
    partner_id = fields.Many2one( 'res.partner', string='Customer', domain="[('is_company','=',True)]" )
    state = fields.Selection([
        ('Requested', 'Requested'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Renewal', 'Renewal')
    ], default='Requested', tracking=True)
    employee_id = fields.Many2one('hr.employee',  string='Employee', default=lambda self: self.env.user.sudo().employee_id.id )
    manager_user_id = fields.Many2one('res.users', string='Manager', default=lambda self: self.env.user.sudo().employee_id.parent_id.user_id.id  if self.env.user.sudo().employee_id.parent_id else False )
    access_request_date = fields.Date()
    integrated_access_request_ids = fields.One2many('integrated.access.request','emp_access_req_id')
    is_access = fields.Boolean( compute="_compute_is_access" )


    def _compute_is_access(self):
        """
           Compute whether the current user has permission to access or approve
           the request based on admin rights, managerial hierarchy, and
           partner access permissions.
        """
        user = self.env.user
        uid = user.id
        employee = user.sudo().employee_id
        is_admin = user.has_group('base.group_system')
        is_manager_role = any([
            user.has_group('hr.group_hr_manager'),
            user.has_group('sales_team.group_sale_manager'),
            user.has_group('project.group_project_manager'),
            is_admin
        ])
        for rec in self:
            rec.is_access = False
            if is_admin:
                rec.is_access = True
                continue
            if not rec.employee_id:
                continue
            manager_ids = rec.employee_id.sudo().get_managers_recursive()
            if uid in manager_ids and user in rec.partner_id.accessible_user_ids:
                rec.is_access = True

    def button_approved(self):
        """
           Approve the access request and grant the employee's user access
           to the selected customer by adding them to accessible_user_ids.
           """
        self.write({
            'state': 'Approved',
            'access_request_date': fields.Date.today(),
        })
        if self.employee_id.sudo().user_id:
            self.partner_id.sudo().accessible_user_ids = [
                (4, self.employee_id.sudo().user_id.id)
            ]

    def button_rejected(self):
        """
            Reject the access request and remove the employee's user
            from the customer's accessible_user_ids.
            """
        self.write({
            'state': 'Rejected',
            'access_request_date': fields.Date.today(),
        })
        if self.employee_id.sudo().user_id:
            self.partner_id.sudo().accessible_user_ids = [
                (3, self.employee_id.sudo().user_id.id)
            ]

    @api.model_create_multi
    def create(self, vals_list):
        """
           Create access request records and automatically generate
           requests for managers if required. Also schedules a mail
           activity for the manager to review the request.
           """
        records = super().create(vals_list)
        for rec in records:
            rec.check_access_for_manager()
            if not self.env.context.get('auto_emp_access_req_approve'):
                manager = rec.employee_id.sudo().parent_id
                user_id = manager.user_id.id if manager and manager.user_id else 2
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': self.env.ref(
                        'mail.mail_activity_data_todo').id,
                    'res_model_id': self.env.ref(
                        'ksc_emp_customer_access.model_emp_access_request').id,
                    'res_id': rec.id,
                    'user_id': user_id,
                    'summary': 'Access Request',
                })
        return records

    def check_access_for_manager(self):
        """
            Automatically create an access request for the manager if the
            manager does not already have access to the customer and no
            existing request is present.
            """
        for rec in self:
            manager_user = rec.manager_user_id
            if not manager_user:
                return
            if manager_user in rec.partner_id.accessible_user_ids:
                return
            manager_employee = manager_user.sudo().employee_id
            if not manager_employee:
                return
            existing = self.env['emp.access.request'].sudo().search_count([
                ('partner_id', '=', rec.partner_id.id),
                ('state', 'in', ['Approved', 'Requested', 'Renewal']),
                ('employee_id', '=', manager_employee.id)
            ])
            if existing:
                return
            next_manager = manager_employee.parent_id
            manager_req = self.sudo().create({
                'partner_id': rec.partner_id.id,
                'state': 'Requested',
                'employee_id': manager_employee.id,
                'manager_user_id': next_manager.user_id.id if next_manager and next_manager.user_id else False
            })
            if self.env.context.get('auto_emp_access_req_approve'):
                manager_req.button_approved()

            return manager_req

    def _emp_access_request_check(self):
        """
                    Scheduled job to validate employee access requests yearly.

                    - Rejects access if the employee user is inactive or the customer
                      is marked as an old customer.
                    - Otherwise moves the request to Renewal state and notifies
                      the employee's manager for re-approval.
        """
        date_year_ago = date.today() + relativedelta(years=-1)
        records = self.search([
                ('state', '=', 'Approved'),
                ('access_request_date', '<=', date_year_ago)
            ])
        for record in records:
                # Get partner status safely
            partner_status = getattr(record.partner_id, 'status', False)
            if (
                        record.employee_id.user_id and not record.employee_id.user_id.active) or partner_status == 'old_customer':
                    record.button_rejected()
            elif record.employee_id.user_id:
                    record.write({
                        'state': 'Renewal',
                        'manager_user_id': record.employee_id.parent_id.user_id.id if record.employee_id.parent_id else False,
                        'access_request_date': fields.Date.today()
                    })
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'res_model_id': self.env.ref('ksc_emp_customer_access.model_emp_access_request').id,
                        'res_id': record.id,
                        'user_id': record.employee_id.parent_id.user_id.id if record.employee_id.parent_id and record.employee_id.parent_id.user_id else 2,
                        'summary': 'Access Request',
                    })