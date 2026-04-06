# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _inherits_join_calc(self, alias, fname, query):
        """
        Changes in the function will help to load alternative lang translation where main lang terms are missing.
        If alternative lang translation are missing too then it will load default eng lang term.
        This term will be for records / fields / menu.
        """
        res = super(Base, self)._inherits_join_calc(alias, fname, query)
        model, field = self, self._fields[fname]
        while field.inherited:
            # retrieve the parent model where field is inherited from
            parent_model = self.env[field.related_field.model_name]
            parent_fname = field.related.split('.')[0]
            # JOIN parent_model._table AS parent_alias ON alias.parent_fname = parent_alias.id
            parent_alias = query.left_join(
                alias, parent_fname, parent_model._table, 'id', parent_fname,
            )
            model, alias, field = parent_model, parent_alias, field.related_field
        if field.translate:
            lang = self.env.lang or 'en_US'
            ######################## Changes for Alternative Lang ###########################
            env_lang_id = self.env['res.lang'].sudo().search([('code', '=', lang)])
            if env_lang_id.alt_language:
                res = f'COALESCE("{alias}"."{fname}"->>\'{lang}\', ' \
                      f'"{alias}"."{fname}"->>\'{env_lang_id.alt_language.code}\', ' \
                      f'"{alias}"."{fname}"->>\'en_US\')'
        return res
