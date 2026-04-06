from odoo import models, fields, api, _


class IntegratedAccessRequest(models.Model):
    _name = 'integrated.access.request'
    _description = 'Integrated Access Request'

    integrated_option = fields.Selection([], string="Integrated Option")
    name = fields.Char(string="Name")
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'), ('rejected', 'Rejected')])
    description = fields.Text(string="Description")
    emp_access_req_id = fields.Many2one('emp.access.request', string="Employee Access Request")

    def approve_integration(self):
        pass

    def reject_integration(self):
        pass
