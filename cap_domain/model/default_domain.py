from odoo import fields, models, api
from odoo.osv import expression


class DefaultDomain(models.Model):
    _name = 'default.domain'
    _description = 'Default Domain Information'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True, string="Active", copy=False)
    is_an_app = fields.Boolean(default=False, string="Is an App", copy=False)
    all_phases = fields.Boolean(default=False, string="For All phases ?", copy=False)
    sequence = fields.Integer(string='Sequence', help="Used to order. Lower is better.")
    used_on_contact = fields.Boolean(string='Used on Contact')

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        """
        This method is used to search domain based on project domain and get context from session test view
        """
        domain = args
        project_id = self.env['project.project'].browse(self.env.context.get('project_id'))
        if project_id:
            domain = expression.AND([
                domain,
                [('id', 'in', project_id.default_domain_ids.ids)]
            ])
        return super(DefaultDomain, self)._name_search(name, domain, operator, limit, order)
