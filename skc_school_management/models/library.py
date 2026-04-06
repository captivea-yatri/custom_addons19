from odoo import models,fields

class Library(models.Model):
    _name = "library"
    _description = "library"

    book_name = fields.Char( copy=False)
    author_name = fields.Char(string="Author Name", required=True)
    edition = fields.Selection(
        [('1', '1st '), ('2', '2nd '), ('3', '3rd ')],
        string="Edition",
        required=True
    )
    chk_in = fields.Date(string="CheckIN date")
    chk_out = fields.Date(string="CheckOUT date")



