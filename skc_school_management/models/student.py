from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class Student(models.Model):
    _name = "student"
    _description = "Student"

    _sql_constraints = [
        ('unique_roll_no', 'unique(roll_no)', 'Roll number must be unique!')
    ]

    name = fields.Char(string="Student Name", required=True)
    roll_no = fields.Char(string="Student Roll No.", required=True)
    age = fields.Integer(string="Student Age", compute="_compute_age", inverse="_inverse_compute_age", store=True)
    dob = fields.Date(string="Date of Birth")
    fees=fields.Integer(string="Student Total Fees", help="Enter Student Total Fees!!")
    std = fields.Selection(
        [('1', '1st Standard'), ('2', '2nd Standard'), ('3', '3rd Standard')],
        string="Standard", required=True
    )
    div = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C')],
        string="Division", required=True
    )
    img = fields.Image(string="Student Image", max_width=100, max_height=100)

    def open_wiz(self):

        return self.env['ir.actions.act_window']._for_xml_id("skc_school_management.update_fees_view_action")
        # return{'type': 'ir.actions.act_window',
        #         'res_model': 'update.student.fees',
        #         'view_mode':'form',
        #         'target': 'new',
        #       }



    @api.depends("dob")
    def _compute_age(self):
        for rec in self:
            if rec.dob:
                today = date.today()
                rec.age = today.year - rec.dob.year - (
                    (today.month, today.day) < (rec.dob.month, rec.dob.day)
                )
            else:
                rec.age = 0

    def _inverse_compute_age(self):
        for rec in self:
            if rec.age:
                today = date.today()
                rec.dob = today - relativedelta(years=rec.age)



