from odoo import api, models


def post_load():
    base_model = models.BaseModel
    if getattr(base_model, '_field_encryption_patched', False):
        return

    original_create = base_model.create
    original_write = base_model.write
    original_read_format = getattr(base_model, '_read_format', None)
    original_name_get = getattr(base_model, 'name_get', None)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('field_encryption_skip'):
            return original_create(self, vals_list)
        vals_list = self.env['field.encryption.rule'].sudo()._encrypt_vals_list(self, vals_list)
        return original_create(self, vals_list)

    def write(self, vals):
        if self.env.context.get('field_encryption_skip'):
            return original_write(self, vals)
        vals = self.env['field.encryption.rule'].sudo()._encrypt_vals_list(self, [vals])[0]
        return original_write(self, vals)

    base_model.create = create
    base_model.write = write

    if original_read_format:
        def _read_format(self, fnames=None, load='_classic_read'):
            rows = original_read_format(self, fnames=fnames, load=load)
            if self.env.context.get('field_encryption_skip'):
                return rows
            return self.env['field.encryption.rule'].sudo()._decrypt_read_result(self, rows, fnames=fnames)

        base_model._read_format = _read_format

    if original_name_get:
        def name_get(self):
            result = original_name_get(self)
            if self.env.context.get('field_encryption_skip'):
                return result
            return self.env['field.encryption.rule'].sudo()._decrypt_name_get(self, result)

        base_model.name_get = name_get

    base_model._field_encryption_patched = True
