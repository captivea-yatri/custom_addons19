from odoo import models, fields

class ResPartnerKsc(models.Model):
    _name = "res.partner.ksc"
    _description = "Customers (KSC)"

    name = fields.Char()
    street1 = fields.Char("Street 1")
    street2 = fields.Char("Street 2")
    country_id = fields.Many2one("res.country.ksc")
    state_id = fields.Many2one("res.state.ksc")
    city_id = fields.Many2one("res.city.ksc")
    zip = fields.Char()
    email = fields.Char()
    mobile = fields.Char()
    phone = fields.Char()
    photo = fields.Image()
    website = fields.Char()
    active = fields.Boolean(default=True)

    parent_id = fields.Many2one('res.partner.ksc')
    child_ids = fields.One2many('res.partner.ksc', 'parent_id')

    address_type = fields.Selection(
        [('invoice', 'Invoice'),
         ('shipping', 'Shipping'),
         ('contact', 'Contact')]
    )
