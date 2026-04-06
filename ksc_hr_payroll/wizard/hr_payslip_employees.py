from odoo import api, fields, models, _

class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'  # define the model, not inherit
    _description = "Payslip Employees Wizard"

    structure_id = fields.Many2one('hr.payroll.structure', string="Salary Structure")
    employee_ids = fields.Many2many('hr.employee', string="Employees")

    @api.onchange('structure_id')
    def ksc_onchange_employee_ids(self):
        for wizard in self:
            if not wizard.structure_id:
                wizard.employee_ids = False
            else:
                employee_ids = self.env['hr.contract'].search(
                    [('structure_type_id.default_struct_id', '=', wizard.structure_id.id),
                     ('state', '=', 'open')]).mapped('employee_id')
                wizard.employee_ids = employee_ids
