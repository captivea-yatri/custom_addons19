from odoo import models, fields

class EmployeeLeaveKSC(models.Model):
    _name = 'employee.leave.ksc'
    _description = 'Employee Leave'

    employee_id = fields.Many2one('employee.ksc', string='Employee')
    department_id = fields.Many2one('employee.department.ksc', string='Department')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    status = fields.Selection([('draft','Draft'),('approved','Approved'),
                               ('refused','Refused'),('cancelled','Cancelled')],
                              default='draft', string='Status')
    leave_description = fields.Char(string='Leave Description', required=True)

    def _get_leaves_domain(self):
        user = self.env.user
        employee = self.env['employee.ksc'].search([('related_user_id','=',user.id)], limit=1)
        if employee.is_manager:
            return [('manager_id','=',employee.id)]
        elif employee.department_id.manager_id.user_ids == user:
            return [('department_id','=',employee.department_id.id)]
        else:
            return [('employee_id','=',employee.id)]
