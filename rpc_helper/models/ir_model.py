# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from odoo import api, fields, models, tools

from odoo.addons.base_sparse_field.models.fields import Serialized
from odoo.exceptions import UserError


class IrModel(models.Model):
    _inherit = "ir.model"

    rpc_config = Serialized(compute="_compute_rpc_config", default={},
        help="Configure RPC config via JSON. "
        "Value must be a list of methods to disable "
        "wrapped by a dict with key `disable`. "
        "Eg: {'disable': ['search', 'do_this']}"
        "To disable all methods, use `{'disable: ['all']}`")
    # Allow editing via UI
    rpc_config_edit = fields.Text(
        help="Configure RPC config via JSON. "
        "Value must be a list of methods to disable "
        "wrapped by a dict with key `disable`. "
        "Eg: {'disable': ['search', 'do_this']}"
        "To disable all methods, use `{'disable: ['all']}`",
        inverse="_inverse_rpc_config_edit",string="Config Value"
    )

    @api.depends("rpc_config_edit")
    def _compute_rpc_config(self):
        """
                Compute the `rpc_config` field based on the editable JSON string field `rpc_config_edit`.
        """
        for rec in self:
            rec.rpc_config = rec._load_rpc_config()

    def _inverse_rpc_config_edit(self):
        """
                Inverse method for the editable RPC configuration field `rpc_config_edit`.
        """
        for rec in self:
            # Make sure options_edit is always readable
            rec.rpc_config_edit = json.dumps(rec.rpc_config or {}, indent=4, sort_keys=True)

    def _load_rpc_config(self):
        """Load RPC configuration safely. Raise user-friendly error if JSON is invalid."""
        text = self.rpc_config_edit or "{}"
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise UserError(
                f"Invalid JSON in RPC configuration for model '{self._name}': {e.msg} "
                f"(line {e.lineno}, column {e.colno})"
            )
        # Optional: validate structure
        if not isinstance(data, dict) or ("disable" in data and not isinstance(data["disable"], list)):
            raise UserError(
                f"RPC configuration must be a dict with optional 'disable' list for model '{self._name}'."
            )
        return data

    @tools.ormcache("model")
    def _get_rpc_config(self, model):
        """
                Retrieve the RPC configuration for a specific model.
        """
        rec = self._get(model)
        if self.env.user.has_group('base.group_system'):
            return {}
        return rec.rpc_config or {}
