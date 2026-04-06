from odoo import models, fields, api, Command

class CustomMailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _prepare_mail_values_dynamic(self, res_ids):
        mail_values_all = super()._prepare_mail_values_dynamic(res_ids)
        str1 = ''
        if 'email_from' in self._context:
            mail_values_all[self._context.get('active_id')]['email_from'] = None
            mail_values_all[self._context.get('active_id')]['email_from'] = self._context['email_from']
        if 'email_cc' in self._context:
            for rec in self._context['email_cc']:
                if len(str1) == 0:
                    str1 += rec
                else:
                    str1 += ', ' + rec
            mail_values_all[self._context.get('active_id')]['email_cc'] = str1
        if 'email_to' in self._context:
            mail_values_all[self._context.get('active_id')]['recipient_ids'] = None
            mail_values_all[self._context.get('active_id')]['email_to'] = self._context['email_to']
        if 'reply_to' in self._context:
            mail_values_all[self._context.get('active_id')]['reply_to'] = self._context['reply_to']
        if 'is_notification' in self._context:
            mail_values_all[self._context.get('active_id')]['is_notification'] = self._context['is_notification']
        return mail_values_all
