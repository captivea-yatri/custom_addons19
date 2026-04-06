from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cron_email_recipient_ids = fields.Many2many('res.users','res_config_settings_user_rel','config_setting_id','user_id',domain=[('share', '=', False),('active', '=', True)], string="Cron Email Recipient : ",company_dependent=False)

    @api.model
    def get_values(self):
        """
            Retrieve saved cron email recipients from ir.config_parameter
            and return them in the settings form.
        """
        res = super(ResConfigSettings, self).get_values()
        cron_email_recipient_ids = self.env['ir.config_parameter'].sudo().get_param('cap_critical_schedule_action.cron_email_recipient_ids')
        if cron_email_recipient_ids:
            res.update({
                'cron_email_recipient_ids': [(6, 0, list(map(int, cron_email_recipient_ids.split(','))))],
            })
        return res

    def set_values(self):
        """
            Save selected cron email recipients to ir.config_parameter
            for persistent storage.
        """
        super(ResConfigSettings, self).set_values()
        user_ids = self.cron_email_recipient_ids.ids
        if user_ids:
            self.env['ir.config_parameter'].sudo().set_param('cap_critical_schedule_action.cron_email_recipient_ids', ','.join(map(str, user_ids)))
        else:
            self.env['ir.config_parameter'].sudo().set_param('cap_critical_schedule_action.cron_email_recipient_ids', '')
