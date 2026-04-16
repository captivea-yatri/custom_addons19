import logging
import os

from cryptography.fernet import Fernet, InvalidToken

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class FieldEncryptionRule(models.Model):
    _name = 'field.encryption.rule'
    _description = 'Field Encryption Rule'
    _order = 'model_model, field_name'

    _ENCRYPTION_PREFIX = 'odoo-fernet$'

    name = fields.Char(compute='_compute_name', store=True)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    model_model = fields.Char(related='model_id.model', store=True, readonly=True)
    field_id = fields.Many2one('ir.model.fields', required=True, ondelete='cascade')
    field_name = fields.Char(related='field_id.name', store=True, readonly=True)
    field_label = fields.Char(related='field_id.field_description', store=True, readonly=True)
    field_type = fields.Char(compute='_compute_field_type', store=True, readonly=True)

    def _compute_field_type(self):
        for record in self:
            record.field_type = str(record.field_id.ttype)  # Convert to string if necessary
    notes = fields.Text()

    _sql_constraints = [
        (
            'field_encryption_rule_unique_field',
            'unique(model_id, field_id)',
            'Only one encryption rule is allowed per model field.',
        )
    ]

    @api.depends('model_id', 'field_id')
    def _compute_name(self):
        for record in self:
            if record.model_id and record.field_id:
                record.name = f'{record.model_model}.{record.field_name}'
            else:
                record.name = False

    @api.constrains('model_id', 'field_id')
    def _check_field_is_supported(self):
        supported_types = self._supported_field_types()
        for record in self:
            if not record.model_id or not record.field_id:
                continue
            if record.field_id.model_id != record.model_id:
                raise ValidationError(_('Selected field does not belong to the chosen model.'))
            if record.field_id.ttype not in supported_types:
                raise ValidationError(
                    _('Only stored Char, Text, and HTML fields are supported for encryption.')
                )
            if not record.field_id.store:
                raise ValidationError(_('Only stored fields can be encrypted.'))

    @api.model
    def _supported_field_types(self):
        return {'char', 'text', 'html'}

    @api.model
    def _excluded_models(self):
        return {'field.encryption.rule', 'ir.model', 'ir.model.fields'}

    @api.model
    def _get_active_rule_map(self, model_name):
        if not model_name or model_name in self._excluded_models():
            return {}
        rows = (
            self.sudo()
            .with_context(field_encryption_skip=True)
            .search_read(
                [('active', '=', True), ('model_model', '=', model_name)],
                ['field_name', 'field_type'],
            )
        )
        return {row['field_name']: row for row in rows if row.get('field_name')}

    @api.model
    def _get_secret_key(self):
        running_env = config.get('running_env')
        env_names = []
        option_names = []

        if running_env:
            env_names.append(f'FIELD_ENCRYPTION_KEY_{running_env.upper()}')
            option_names.append(f'field_encryption_key_{running_env}')

        env_names.append('FIELD_ENCRYPTION_KEY')
        option_names.append('field_encryption_key')

        for env_name in env_names:
            key = os.getenv(env_name)
            if key:
                return key.encode() if isinstance(key, str) else key

        for option_name in option_names:
            key = config.get(option_name)
            if key:
                return key.encode() if isinstance(key, str) else key

        if running_env:
            raise ValidationError(
                _(
                    "Missing encryption key. Set env '%s' or 'FIELD_ENCRYPTION_KEY', or add 'field_encryption_key_%s' or 'field_encryption_key' to odoo.conf."
                )
                % (running_env.upper() and f'FIELD_ENCRYPTION_KEY_{running_env.upper()}', running_env)
            )
        raise ValidationError(
            _("Missing encryption key. Set env 'FIELD_ENCRYPTION_KEY' or add 'field_encryption_key' to odoo.conf.")
        )

    @api.model
    def _get_cipher(self):
        try:
            return Fernet(self._get_secret_key())
        except Exception as exc:
            raise ValidationError(
                _('Invalid encryption key. Generate a valid Fernet key before using this module.')
            ) from exc

    @api.model
    def _encrypt_value(self, value):
        if value in (False, None, '') or not isinstance(value, str):
            return value
        if value.startswith(self._ENCRYPTION_PREFIX):
            return value
        token = self._get_cipher().encrypt(value.encode('utf-8')).decode('utf-8')
        return f'{self._ENCRYPTION_PREFIX}{token}'

    @api.model
    def _decrypt_value(self, value):
        if value in (False, None, '') or not isinstance(value, str):
            return value
        if not value.startswith(self._ENCRYPTION_PREFIX):
            return value
        token = value[len(self._ENCRYPTION_PREFIX) :].encode('utf-8')
        try:
            return self._get_cipher().decrypt(token).decode('utf-8')
        except InvalidToken:
            _logger.warning('Unable to decrypt field value with current configured key.')
            return value

    @api.model
    def _encrypt_vals_list(self, recordset, vals_list):
        rules = self._get_active_rule_map(recordset._name)
        if not rules:
            return vals_list

        prepared_vals_list = []
        for vals in vals_list:
            prepared_vals = dict(vals)
            for field_name in rules:
                if field_name in prepared_vals:
                    prepared_vals[field_name] = self._encrypt_value(prepared_vals[field_name])
            prepared_vals_list.append(prepared_vals)
        return prepared_vals_list

    @api.model
    def _decrypt_read_result(self, recordset, rows, fnames=None):
        rules = self._get_active_rule_map(recordset._name)
        if not rules or not rows:
            return rows

        decrypted_fields = set(rules)
        if fnames:
            decrypted_fields &= set(fnames)

        for row in rows:
            for field_name in decrypted_fields:
                if field_name in row:
                    row[field_name] = self._decrypt_value(row[field_name])
        return rows

    @api.model
    def _decrypt_name_get(self, recordset, name_get_result):
        if not name_get_result:
            return name_get_result

        rules = self._get_active_rule_map(recordset._name)
        rec_name = getattr(recordset, '_rec_name', None) or 'name'

        if rec_name not in rules:
            return name_get_result

        return [
            (record_id, self._decrypt_value(name) if isinstance(name, str) else name)
            for record_id, name in name_get_result
        ]

    def action_encrypt_existing_records(self):
        total_updated = 0
        for rule in self:
            model = self.env[rule.model_model].sudo().with_context(field_encryption_skip=True)
            records = model.search([(rule.field_name, '!=', False)])
            for record in records:
                current_value = record[rule.field_name]
                encrypted_value = rule._encrypt_value(current_value)
                if encrypted_value != current_value:
                    record.with_context(field_encryption_skip=True).write(
                        {rule.field_name: encrypted_value}
                    )
                    total_updated += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Field encryption'),
                'message': _('Encrypted %s existing record values.') % total_updated,
                'type': 'success',
                'sticky': False,
            },
        }
