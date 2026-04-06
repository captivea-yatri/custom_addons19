from odoo import api
from odoo import fields
from odoo import models


class ProductTag(models.Model):
    _description = 'Product Tags'
    _inherit = "product.tag"
    _parent_store = False
    _parent_order = 'name'
    _order = 'parent_left'

    name = fields.Char('Tag Name', required=True, translate=True)
    active = fields.Boolean(help='The active field allows you to hide the tag without removing it.', default=True)
    parent_id = fields.Many2one(string='Parent Tag', comodel_name='product.tag', index=True, ondelete='cascade')
    child_ids = fields.One2many(string='Child Tags', comodel_name='product.tag', inverse_name='parent_id')
    parent_left = fields.Integer('Left Parent', index=True)
    parent_right = fields.Integer('Right Parent', index=True)

    image = fields.Binary('Image')

    def name_get(self):
        """ Return the tags' display name, including their direct parent. """
        res = []
        for record in self:
            current = record
            name = current.name
            while current.parent_id:
                name = '%s / %s' % (current.parent_id.name, name)
                current = current.parent_id
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        tags = self.search(args, limit=limit)
        return tags.name_get()





class ProductTemplate(models.Model):
    _inherit = "product.template"

    tag_ids = fields.Many2many(string='Tags',
                               comodel_name='product.tag',
                               relation='product_product_tag_rel',
                               column1='tag_id',
                               column2='product_id')







