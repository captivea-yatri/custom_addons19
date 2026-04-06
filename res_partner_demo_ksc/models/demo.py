from odoo import models, fields

class Demo1(models.Model):
    _name = "demo"
    _description = "demo1"

    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email")
    street1 = fields.Char(string="Street1")
    street2 = fields.Char(string="Street2")
    city = fields.Char(string="City", required=True)
    state = fields.Char(string="State", required=True)
    zip_code = fields.Char(string="Zipcode")
    country = fields.Char(string="Country", required=True)
    dob = fields.Date(string="DOB")
    age = fields.Integer(string="Age")
    weight = fields.Float(string="Weight")
    description = fields.Text(string="Description")
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('transgender', 'Transgender')],
        string="Gender",
        required=True
    )
    details = fields.Html(string="Details")
    js_spectacles = fields.Boolean(string="Js_spectacles ")
    photo = fields.Binary(string="Photo")
