from odoo import models, fields, api, _, Command, SUPERUSER_ID
import base64
from datetime import date
from werkzeug.urls import url_join
from odoo.tools import config, get_lang, is_html_empty


class SessionTest(models.Model):
    _name = 'session.test'
    _inherit = ['session.test', 'mail.thread','mail.activity.mixin', 'portal.mixin', 'utm.mixin']

    sign_request_id = fields.Many2one('sign.request', readonly=True, copy=False)
    hide_button_sign_and_validate = fields.Boolean(default=True)
    is_assigned_user = fields.Boolean(default=False, compute="check_assigned_user")


    def _compute_access_url(self):
        super()._compute_access_url()
        for test in self:
            test.access_url = f'/my/project_tests/{test.project_id.id}'


    @api.model_create_multi
    def create(self, vals):
        res = super(SessionTest, self).create(vals)
        partner_ids = []
        partner_ids.append(res.assigned_user_id.partner_id.id)
        partner_ids.append(res.signer_id.partner_id.id)
        partner_ids.append(res.sudo().project_id.user_id.partner_id.id)
        res.sudo().message_partner_ids = [(4, rec) for rec in partner_ids]
        return res

    def check_assigned_user(self):
        """
        This method is used for hide button of close and skip session test for user as per assigned user
        """
        for rec in self:
            rec.is_assigned_user = True if rec.assigned_user_id.id == self.env.user.id else False
            if rec.is_assigned_user and rec.status in ['draft','sent']:
                rec.status = 'in progress'

    def action_open_session_test(self, session_test, project_test_id):
        """
        This method is used to open session test list and form view
        """
        action = self.env["ir.actions.actions"]._for_xml_id("cap_project_test_portal.action_session_test_portal")
        action['domain'] = [('id', 'in', session_test.ids)]
        action['context'] = {'default_project_id': project_test_id.id}
        return action

    def action_open_session_test_launch(self, project_test_id):
        """
        This method is used to open session launch view from smart tab
        """
        action = self.env["ir.actions.actions"]._for_xml_id(
            "cap_project_test_portal.action_session_test_portal_for_launch_session")
        action['res_id'] = self.id
        action['domain'] = [('id', '=', self.id)]
        action['context'] = {'default_project_id': project_test_id.id}
        return action

    def send_email(self):
        """
        This method is used to send mail to assined user of session test
        """
        report_template_id = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            "cap_project_test_portal.report_session_test",
            res_ids=self.ids)
        data_record = base64.b64encode(report_template_id[0])
        today_date = date.today()
        ir_values = {
            'name': self.project_id.name + " - " + self.name + " - " + today_date.strftime("%Y-%m-%d") + ".pdf",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].sudo().create(ir_values)

        sign_template_id = self.env['sign.template'].sudo().create({'attachment_id': data_id.id, 'active': False})

        self.env['sign.item'].sudo().create({
            'type_id': self.env.ref('sign.sign_item_type_signature').id,
            'required': True,
            'responsible_id': self.env.ref('sign.sign_item_role_default').id,
            'page': 1,
            'posX': 0.100,
            'posY': 0.850,
            'template_id': sign_template_id.id,
            'width': 0.200,
            'height': 0.050,
        })

        sign_request = self.env['sign.request'].with_user(SUPERUSER_ID).with_context(no_sign_mail=True).create({
            'template_id': sign_template_id.id,
            'reference': sign_template_id.display_name,
            'request_item_ids': [Command.create({
                'partner_id': self.sudo().signer_id.partner_id.id,
                'role_id': self.env.ref('sign.sign_item_role_default').id,
            })],
            'subject': sign_template_id.display_name,
            'message': "Sign to validate the session test : {}".format(self.name),
            'attachment_ids': [Command.set(data_id.ids)],
        })
        sign_request.sudo().request_item_ids._send_signature_access_mail()
        self.sign_request_id = sign_request.id
        sign_request.with_user(SUPERUSER_ID).go_to_signable_document()
        self.hide_button_sign_and_validate = True
        sign_request_item = sign_request.request_item_ids[0]
        partner_lang = get_lang(self.env, lang_code=sign_request_item.partner_id.lang).code
        self.prepare_chatter_mail_tracking(sign_request_item,sign_request,partner_lang, reference=sign_request.subject,
                                           sign_template='sign.sign_template_mail_request')

        return {
            'effect': {
                'fadeout': 'slow',
                'message': """Email send Successfully! \n\n
                           Check your Mailbox to Sign the document""",
                'type': 'rainbow_man',
            }
        }

    def prepare_chatter_mail_tracking(self,sign_request_item, sign_request, partner_lang, reference, sign_template):
        """
        # here prepare the body for chatter mail for tracking
        @return:
        """
        signers = [{'name': signer.partner_id.name, 'email': signer.signer_email, 'id': signer.partner_id.id} for
                   signer
                   in sign_request_item]
        timestamp = sign_request_item._generate_expiry_link_timestamp()
        expiry_hash = sign_request_item._generate_expiry_signature(sign_request_item.id, timestamp)
        body = self.env['ir.qweb'].sudo()._render(sign_template, {
            'record': sign_request_item,
            'link': url_join(sign_request_item.get_base_url(),
                             "sign/document/mail/%(request_id)s/%(access_token)s?timestamp=%(timestamp)s&exp=%(exp)s" % {'request_id': sign_request.id,
                                                                                     'access_token': sign_request_item.sudo().access_token,
                                                                                     'timestamp': timestamp,
                                                                                     'exp': expiry_hash}),
            'subject': reference,
            'recipient_id': sign_request.request_item_ids.partner_id.id,
            'recipient_name': sign_request.request_item_ids.partner_id.name,
            'signers': signers,
            'body': sign_request.message if not is_html_empty(sign_request.message) else False,
            'use_sign_terms': self.env['ir.config_parameter'].sudo().get_param('sign.use_sign_terms'),
            'user_signature': sign_request.create_uid.signature,
        }, lang=partner_lang, minimal_qcontext=True)
        self.sudo().message_post(body=body)


    def action_create_execution_test(self):
        super(SessionTest, self).action_create_execution_test()
        self.hide_button_sign_and_validate = False

    def action_launch_session(self):
        """
        This method is used to open report action from session test launch session test
        """
        self.ensure_one()

        # Check logged-in user and status
        if (
                self.assigned_user_id
                and self.env.user == self.assigned_user_id
                and self.status == 'draft'
        ):
            self.write({'status': 'in progress'})

        action = {
            "type": "ir.actions.act_url",
            "url": "/my/test/{}".format(self.id),
            "target": "self",
        }
        return action
