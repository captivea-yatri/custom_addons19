from odoo import fields,models

class UpdateStudentFees(models.TransientModel):
    _name = 'update.student.fees'
    _description = 'Student Fees Wizard'

    total_fees=fields.Float(string="Total Fees")

    def update_student_fees(self):
        print("Successfully fees updated using wizard")

        self.env['student'].browse(self._context.get('active_ids')).update({'fees': self.total_fees})
        return True