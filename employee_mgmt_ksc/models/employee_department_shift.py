from odoo import models, fields

class EmployeeShiftKSC(models.Model):
    _name = 'employee.department.shift.ksc'
    _description = 'Employee Shift'
    _rec_name = 'shift'

    shift = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon'),
                              ('evening', 'Evening'), ('night', 'Night')], required=True)
    employee_ids = fields.One2many('employee.ksc', 'shift_id', string='Employees')
