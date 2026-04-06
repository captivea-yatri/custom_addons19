# -*- coding: utf-8 -*-
import re
import logging

from odoo import api, fields, models, tools, _
# from odoo.modules.module import get_module_resource
from odoo.tools import config
from odoo.addons.base.models.ir_ui_view import get_view_arch_from_file

_logger = logging.getLogger(__name__)


class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.depends('arch_db', 'arch_fs', 'arch_updated')
    @api.depends_context('read_arch_from_file', 'lang', 'edit_translations', 'check_translations')
    def _compute_arch(self):
        """

             Overrides Odoo’s core `_compute_arch` to dynamically translate XML architecture (`arch_db`)
             using the active language and an optional *alternative language* fallback.
               Logic:
                   1. Get the user’s current language and check if it defines an `alt_language`.
                   2. If no alternative is configured → fall back to the original Odoo method.
                   3. If `read_arch_from_file` is True or dev mode is active:
                       - Load view XML from file using `get_view_arch_from_file`.
                       - Replace any XMLID references (`%(xml_id)d`) with actual record IDs.
                       - Build a translation dictionary between English → target language.
                       - Apply translations to the view architecture.
                   4. Call `get_alternative_arch()` to merge alternative language translations
                      if any terms are missing.
                   5. Finally, assign the computed XML (`db_view` or fallback `arch_db`) to `view.arch`.

               """
        lang = self.env.lang or 'en_US'
        env_lang_id = self.env['res.lang'].sudo().search([('code', '=', lang)])
        if not env_lang_id.alt_language or not self:
            return super(View, self)._compute_arch()

        def resolve_external_ids(arch_fs, view_xml_id):
            def replacer(m):
                xmlid = m.group('xmlid')
                if '.' not in xmlid:
                    xmlid = '%s.%s' % (view_xml_id.split('.')[0], xmlid)
                return m.group('prefix') + str(self.env['ir.model.data']._xmlid_to_res_id(xmlid))
            return re.sub(r'(?P<prefix>[^%])%\((?P<xmlid>.*?)\)[ds]', replacer, arch_fs)

        env_en = self.with_context(edit_translations=None, lang='en_US').env
        env_lang = self.with_context(lang=lang).env
        field_arch_db = self._fields['arch_db']

        for view in self:
            arch_fs = None
            read_file = self._context.get('read_arch_from_file') or \
                        ('xml' in config['dev_mode'] and not view.arch_updated)
            if read_file and view.arch_fs and (view.xml_id or view.key):
                xml_id = view.xml_id or view.key
                # new safe resource loader in Odoo 19
                module_name, *path_parts = view.arch_fs.split('/')
                fullpath = get_module_resource(module_name, *path_parts)
                if fullpath:
                    arch_fs = get_view_arch_from_file(fullpath, xml_id)
                    if arch_fs:
                        arch_fs = resolve_external_ids(arch_fs, xml_id).replace('%%', '%')
                        translation_dictionary = field_arch_db.get_translation_dictionary(
                            view.with_env(env_en).arch_db,
                            {lang: view.with_env(env_lang).arch_db}
                        )
                        arch_fs = field_arch_db.translate(
                            lambda term: translation_dictionary[term][lang],
                            arch_fs
                        )
                else:
                    _logger.warning("View %s: Full path [%s] cannot be found.", xml_id, view.arch_fs)
                    arch_fs = False

            # Apply fallback with alternative language logic
            db_view = view.get_alternative_arch(env_lang_id, env_en, env_lang, field_arch_db, lang)
            view.arch = db_view or view.arch_db

    def _inverse_arch(self):
        """
                    Ensures that view architecture (`arch`) updates are properly saved back into
                    `arch_db` and `arch_fs` fields while respecting alternative language fallbacks.

                Logic:
                    1. If the current language does not define an alternative → call super().
                    2. For each view:
                        - Write new architecture (`arch_db`) to DB.
                        - If the installation context contains `install_filename`, update `arch_fs` accordingly.
                    3. Recompute the merged architecture again using `get_alternative_arch`
                       to apply translation consistency across languages.
                    4. Invalidate cached values for the `arch` field to reflect new data.

                Returns:
                    None — modifies current records in place.
                """
        lang = self.env.lang or 'en_US'
        env_lang_id = self.env['res.lang'].sudo().search([('code', '=', lang)])
        if not env_lang_id.alt_language or not self:
            return super(View, self)._inverse_arch()

        for view in self:
            data = dict(arch_db=view.arch)
            if 'install_filename' in self._context:
                # old get_resource_from_path removed in Odoo 19 — we safely skip it
                filename = self._context['install_filename']
                if '/' in filename:
                    module, *path_parts = filename.split('/')
                    data['arch_fs'] = '/'.join([module] + path_parts)
                    data['arch_updated'] = False
            view.write(data)

            if view.arch_db:
                env_en = self.with_context(edit_translations=None, lang='en_US').env
                env_lang = self.with_context(lang=lang).env
                field_arch_db = self._fields['arch_db']
                db_view = view.get_alternative_arch(env_lang_id, env_en, env_lang, field_arch_db, lang)
                view.arch = db_view or view.arch_db

        self.invalidate_recordset(['arch'])

    def get_alternative_arch(self, env_lang_id, env_en, env_lang, field_arch_db, lang):
        """
                    Constructs a translation dictionary that fills missing translations from an
                    alternative language, ensuring smoother multilingual UX.
                Logic:
                    1. Load view architecture in three environments:
                       - English (`env_en`)
                       - Current language (`env_lang`)
                       - Alternative language (`alt_env_lang`)
                    2. Build translation dictionaries from English → Current and English → Alternative.
                    3. For every English term:
                       - If the translation in current language is incomplete or identical in length,
                         replace it with the alternative language translation.
                    4. Translate the final architecture using the updated dictionary.
                Args:
                    env_lang_id (record): Current language record (`res.lang`).
                    env_en (Environment): Environment with English context.
                    env_lang (Environment): Environment with current language context.
                    field_arch_db (Field): Field object for `arch_db` (provides translation helpers).
                    lang (str): Current language code (e.g., 'fr_FR').
                """
        alt_env_lang = self.with_context(lang=env_lang_id.alt_language.code).env
        db_view = self.arch_db
        db_view_en = self.with_env(env_en).arch_db
        db_view_env_lang = self.with_env(env_lang).arch_db
        db_view_alt_lang = self.with_env(alt_env_lang).arch_db

        current_lang_dict = field_arch_db.get_translation_dictionary(db_view_en, {lang: db_view_env_lang})
        alt_lang_trans_dict = field_arch_db.get_translation_dictionary(
            db_view_en, {env_lang_id.alt_language.code: db_view_alt_lang}
        )

        for term_en, translations in current_lang_dict.items():
            for cur_lang, cur_term in translations.items():
                if len(term_en) == len(cur_term):
                    alt_term = alt_lang_trans_dict.get(term_en, {}).get(env_lang_id.alt_language.code)
                    if alt_term:
                        translations[cur_lang] = alt_term

        db_view = field_arch_db.translate(lambda term: current_lang_dict[term][lang], db_view)
        return db_view
