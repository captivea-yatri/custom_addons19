from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    crm_ai_enabled = fields.Boolean(
        string="Enable CRM AI Dynamic Tagging",
        config_parameter="crm_ai_dynamic_tagging.enabled",
    )
    crm_ai_api_url = fields.Char(
        string="AI API URL",
        config_parameter="crm_ai_dynamic_tagging.api_url",
    )
    crm_ai_api_key = fields.Char(
        string="AI API Key",
        config_parameter="crm_ai_dynamic_tagging.api_key",
    )
    crm_ai_model = fields.Char(
        string="AI Model",
        config_parameter="crm_ai_dynamic_tagging.model",
        default="gpt-4.1-mini",
    )
    crm_ai_timeout = fields.Integer(
        string="Timeout (seconds)",
        config_parameter="crm_ai_dynamic_tagging.timeout",
        default=30,
    )
    crm_ai_max_new_tags = fields.Integer(
        string="Max New Tags Per Lead",
        config_parameter="crm_ai_dynamic_tagging.max_new_tags",
        default=1,
    )
    crm_ai_process_on_create = fields.Boolean(
        string="Queue on Create",
        config_parameter="crm_ai_dynamic_tagging.process_on_create",
        default=True,
    )
    crm_ai_process_on_write = fields.Boolean(
        string="Queue on Update",
        config_parameter="crm_ai_dynamic_tagging.process_on_write",
        default=True,
    )