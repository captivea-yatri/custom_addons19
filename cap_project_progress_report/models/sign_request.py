from odoo import api, fields, models, SUPERUSER_ID
from werkzeug.urls import url_join
from odoo.tools import config, get_lang, is_html_empty, formataddr, groupby, format_date


class SignRequest(models.Model):
    _inherit = "sign.request"

    project_progress_id = fields.Many2one('project.progress', readonly=True)

    @api.model
    def _message_send_mail(self, body, email_layout_xmlid, message_values, notif_values, mail_values, force_send=False,
                           **kwargs):
        rec = super(SignRequest, self)._message_send_mail(body, email_layout_xmlid, message_values, notif_values,
                                                          mail_values, force_send=False)
        if self.env.context.get('partner_id'):
            rec.email_cc = ", ".join(self.env.context.get('partner_id'))
        return rec

    def _generate_completed_document(self):
        super(SignRequest, self)._generate_completed_document()
        lang = self.project_progress_id.project_id.partner_id.lang
        partner_lang = get_lang(self.env, lang_code=lang).code
        signers = [{'name': signer.partner_id.name, 'email': signer.signer_email, 'id': signer.partner_id.id} for signer
                   in self.request_item_ids]
        base_url = self.get_base_url()
        if self.state == 'signed' and self.project_progress_id:
            timestamp = self.request_item_ids[0]._generate_expiry_link_timestamp()
            expiry_hash = self.request_item_ids[0]._generate_expiry_signature(self.request_item_ids[0].id, timestamp)
            body = self.env['ir.qweb'].sudo()._render('sign.sign_template_mail_completed', {
                'record': self,
                'link': url_join(base_url,
                                 "sign/document/mail/%(request_id)s/%(access_token)s?timestamp=%(timestamp)s&exp=%(exp)s" % {
                                     'request_id': self.id,
                                     'access_token': self.request_item_ids.sudo().access_token,
                                     'timestamp': timestamp,
                                     'exp': expiry_hash
                                 }),
                'subject': '%s signed' % self.reference,
                'recipient_name': self.request_item_ids.partner_id.name,
                'recipient_id': self.request_item_ids.partner_id.id,
                'signers': signers,
                'request_edited': any(log.action == "update" for log in self.sign_log_ids),
            }, lang=partner_lang, minimal_qcontext=True)
            self.project_progress_id.message_post(body=body)
            self.project_progress_id.write({'status': 'signed'})
