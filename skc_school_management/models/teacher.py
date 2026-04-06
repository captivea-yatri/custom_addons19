from odoo import models, fields

class Teacher(models.Model):
    _name = "teacher"
    _description = "teacher"

    name = fields.Char(string="Teacher Name", required=True)
    age = fields.Integer(string="Teacher Age", required=True)
    dob = fields.Date(string="DOB")
    std = fields.Selection(
        [('1', '1st Standard'), ('2', '2nd Standard'), ('3', '3rd Standard')],
        string="STD",
        required=True
    )
    div = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C')],
        string="DIV",
        required=True
    )
    sub = fields.Selection(
        [('Maths', 'Maths'), ('Biology', 'Biology'), ('Chem', 'Chem')],
        string="sub",
        required=True
    )
