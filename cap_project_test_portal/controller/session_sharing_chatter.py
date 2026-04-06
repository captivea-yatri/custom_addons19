from werkzeug.exceptions import Forbidden
from odoo import http, _
from odoo.http import request
from .session_test_portal import SessionTestPortal
from odoo import SUPERUSER_ID


class SessionSharingChatter(http.Controller):

    def _check_session_access_and_get_token(self, project_id, res_model, res_id, token):
        """
        Check portal access and return the session token if allowed.
        """
        project_sudo = SessionTestPortal._document_check_access(self, 'project.project', project_id, token)
        can_access = project_sudo and res_model == 'session.test' and project_sudo.with_user(SUPERUSER_ID)._check_project_sharing_access()
        session = None
        if can_access:
            session = request.env['session.test'].sudo().search(
                [('id', '=', res_id), ('project_id', '=', project_sudo.id)]
            )
        if not can_access or not session:
            raise Forbidden()
        return session[session._mail_post_token_field] if session else None

    @http.route('/my/session/<int:session_id>/chatter/init', type='json', auth='user', website=True)
    def portal_chatter_init(self, session_id, **kwargs):
        """
        Initialize portal chatter for session.test
        """
        session = request.env['session.test'].sudo().browse(session_id)
        if not session.exists():
            raise Forbidden()

        project_id = session.project_id.id
        token = self._check_session_access_and_get_token(project_id, 'session.test', session_id, kwargs.get('token'))
        kwargs['token'] = token
        # Fetch messages manually
        messages = session.message_ids.sorted('date')
        return {
            'messages': [
                {
                    'author': m.author_id.name,
                    'body': m.body,
                    'date': m.date,
                    'attachments': [
                        {'name': att.name, 'url': f'/web/content/{att.id}/{att.name}'}
                        for att in m.attachment_ids
                    ],
                }
                for m in messages
            ]
        }

    @http.route('/my/session/<int:session_id>/chatter/fetch', type='json', auth='user', website=True)
    def portal_message_fetch(self, session_id, limit=10, after=None, before=None, **kw):
        """
        Fetch session.test chatter messages in portal
        """
        session = request.env['session.test'].sudo().browse(session_id)
        if not session.exists():
            raise Forbidden()

        kw['token'] = session.project_id.sudo().access_token
        messages = session.message_ids.sorted('date')  # you can implement limit, after, before if needed

        return {
            'messages': [
                {
                    'author': m.author_id.name,
                    'body': m.body,
                    'date': m.date,
                    'attachments': [
                        {'name': att.name, 'url': f'/web/content/{att.id}/{att.name}'}
                        for att in m.attachment_ids
                    ],
                }
                for m in messages
            ]
        }
