from odoo import models, fields

class EmployeeDepartmentKSC(models.Model):
    _name = 'employee.department.ksc'
    _description = 'Department'

    name = fields.Char(string='Department Name', required=True)
    employee_ids = fields.One2many('employee.ksc', 'department_id', string='Employees')
    manager_id = fields.Many2one('res.users', string='Department Manager')
