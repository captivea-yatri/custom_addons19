from odoo import models, fields, api
from odoo.exceptions import UserError

class EmployeeKSC(models.Model):
    _name = 'employee'
    _description = 'KSC Employee'

    name = fields.Char(string="Employee Name", required=True)
    department_name = fields.Char(string="Department Name")
    job_position = fields.Char(string="Job Position")
    salary = fields.Float(string="Salary", digits=(6, 2))
    hire_date = fields.Date(string="Hire Date")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('trans', 'Transgender'),
    ], string="Gender")

    job_type = fields.Selection([
        ('permanent', 'Permanent'),
        ('adhoc', 'Ad Hoc'),
    ], string="Job Type")

    # ✅ Override create method
    @api.model
    def create(self, vals):
        print("Before super() ------------")
        print("self:", self)        # <class 'employee'> model reference (no record yet)
        print("vals:", vals)        # The dictionary of values to insert

        # Actual record creation
        res = super(EmployeeKSC, self).create(vals)

        print("After super() -------------")
        print("res (new record):", res)      # recordset of new record
        print("res.id:", res.id)             # record ID now available
        print("vals (original):", vals)      # same dictionary passed to create
        print("self (still model):", self)   # model reference remains same

        return res

    def write(self, vals):
        for rec in self:
            if 'salary' in vals and vals['salary'] != rec.salary:
                print(f"Salary changed for {rec.name}: {rec.salary} → {vals['salary']}")
        return super(EmployeeKSC, self).write(vals)

    def unlink(self):
        print("⚙️ UNLINK method CALLED ⚙️")
        for rec in self:
            print(f"Trying to delete record: {rec.name}")
            if rec.job_type == 'permanent':
                raise UserError(f"You cannot delete permanent employee: {rec.name}")
        result = super(EmployeeKSC, self).unlink()
        print("✅ Record(s) deleted successfully.")
        return result





