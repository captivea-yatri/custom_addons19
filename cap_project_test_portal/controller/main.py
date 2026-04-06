from odoo.addons.sign.controllers.main import Sign
from odoo import http, models
from odoo.http import request
from werkzeug.urls import url_join
from odoo.tools import config, get_lang, is_html_empty, formataddr, groupby, format_date


class SignInherit(Sign):

    @http.route([
        '/sign/sign/<int:sign_request_id>/<token>',
        '/sign/sign/<int:sign_request_id>/<token>/<sms_token>'
    ], type='json', auth='public')
    def sign(self, sign_request_id, token, sms_token=False, signature=None, **kwargs):
        """This method is override from sign module to add attachment and set status as signed on session test """
        rec = super(SignInherit, self).sign(sign_request_id, token, sms_token=sms_token, signature=signature,
                                            **kwargs)
        request_item_sudo = http.request.env['sign.request.item'].sudo().search([
            ('sign_request_id', '=', sign_request_id),
            ('access_token', '=', token),
        ], limit=1)

        session_test_id = request.env['session.test'].search([('sign_request_id', '=', sign_request_id)])
        if session_test_id and request_item_sudo.sign_request_id.completed_document_attachment_ids:
            session_test_id.write({
                'attachment_id': request_item_sudo.sign_request_id.completed_document_attachment_ids[0].id,
                'status': 'signed'
            })

            ############################ here prepare the body for chatter mail for tracking ######################################
            sign_request_id = request.env['sign.request'].browse(sign_request_id)
            lang = request_item_sudo.partner_id.lang
            if len(request_item_sudo) > 1 and request.env and request.env.user:
                lang = request.env.user.lang
            partner_lang = get_lang(request.env, lang_code=lang).code
            session_test_id.with_context(body_mail_chatter=True).prepare_chatter_mail_tracking(
                sign_request_item=request_item_sudo, sign_request=sign_request_id, partner_lang=partner_lang,
                reference='%s signed' % sign_request_id.reference, sign_template='sign.sign_template_mail_completed')
        return rec
