from odoo import fields,models

class test_abstract(models.AbstractModel):
    _name = 'test.abstract'
    _description = 'Test Abstract'

    name = fields.Char(string='Name')