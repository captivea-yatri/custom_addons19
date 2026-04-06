from odoo import models, fields, api

class EmployeeKSC(models.Model):
    _name = 'employee.ksc'
    _description = 'Employee'

    name = fields.Char(string='Employee Name', required=True)
    department_id = fields.Many2one('employee.department.ksc', string='Department', required=True)
    shift_id = fields.Many2one('employee.department.shift.ksc', string='Shift', required=True)
    job_position = fields.Char(string='Job Position')
    salary = fields.Float(string='Salary', digits=(6, 2))
    hire_date = fields.Date(string='Hire Date')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('transgender', 'Transgender')])
    job_type = fields.Selection([('permanent', 'Permanent'), ('adhoc', 'Ad Hoc')])
    is_manager = fields.Boolean(string='Is Manager')
    manager_id = fields.Many2one('employee.ksc', string='Manager', domain=[('is_manager', '=', True)],
                                 ondelete='set null')
    related_user_id = fields.Many2one('res.users', string='Related User')
    employee_ids = fields.One2many('employee.ksc', 'manager_id', string='Employees', readonly=True)
    increment_percentage = fields.Float(string='Increment %', digits=(6, 2), groups='employee_mgmt_ksc.group_manager')
