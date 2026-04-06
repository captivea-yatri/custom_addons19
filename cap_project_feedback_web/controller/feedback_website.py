from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request, route
from werkzeug.exceptions import Forbidden
from odoo import http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal_thread import PortalChatter
class FeedbackWebsite(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        Feedback = request.env['project.feedback'].sudo()

        # Always compute count
        try:
            project_ids = request.env['project.project'].sudo().search([])
            feedback_count = Feedback.search_count([('project_id', 'in', project_ids.ids)])
        except Exception:
            feedback_count = 0

        values['feedback_count'] = feedback_count
        return values

    @http.route(['/my/feedback', '/my/feedback/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_feedback(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        Project = request.env['project.project']
        domain = self._prepare_project_domain()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name asc'},
        }
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # projects count
        project_count = Project.search_count(domain)

        pager = portal_pager(
            url="/my/feedback",
            url_args={'sortby': sortby},
            total=project_count,
            page=page,
            step=self._items_per_page
        )
        project_ids = Project.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_projects_history'] = project_ids.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'projects': project_ids,
            'page_name': 'feedbacks',
            'default_url': '/my/feedback',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render('cap_project_feedback_web.portal_my_projects_feedback', values)


    @http.route(['/my/feedback/<int:project_id>', '/my/feedback/<int:project_id>/page/<int:page>'],
                type='http',
                auth="public", website=True)
    def portal_my_feedback_sharing(self, project_id=None, access_token=None):
        feedback_ids = request.env['project.feedback'].search([('project_id', '=', project_id)])
        try:
            self._document_check_access('project.project', project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = {'project_id': project_id}
        if feedback_ids.exists():
            values['feedback_ids'] = feedback_ids
        return request.render("cap_project_feedback_web.project_feedback_sharing_portal", values)

    @http.route("/my/project_feedback/<int:project_id>/feedback_sharing", type="http", auth="user", website=True,
                methods=['GET'])
    def render_feedback_backend_view(self, project_id):
        feedback_ids = request.env['project.feedback'].search([('project_id', '=', project_id)])
        session_info = self._prepare_feedbacks_info(feedback_ids, project_id)
        if not session_info:
            return request.redirect('/my')
        return request.render(
            'cap_project_feedback_web.project_feedback_embed',
            {'session_info': session_info},
        )

    def _prepare_feedbacks_info(self, feedback, project_id):
        project_id = request.env['project.project'].browse(project_id)
        session_info = request.env['ir.http'].sudo().session_info()
        user_context = dict(request.env.context) if request.session.uid else {}
        mods = request.env['ir.module.module'].sudo().search([('state', '=', 'installed')]).mapped('name')
        if request.env.lang:
            lang = request.env.lang
            session_info['user_context']['lang'] = lang
            # Update Cache
            user_context['lang'] = lang
        session_info['user_context']['is_created_from_website'] = True
        user_context['is_created_from_website'] = True
        lang = user_context.get("lang")
        cache_hashes = {
            "translations": "auto",
        }
        session_info.update(
            cache_hashes=cache_hashes,
            action_name=feedback.action_open_feedbacks(feedback, project_id),
            # FIXME: See if we prefer to give only the currency that the portal user just need to see the correct information in project sharing
            currencies=request.env['ir.http'].get_currencies(),
            user_companies={
                'current_company': project_id.sudo().company_id.id,
                'allowed_companies': {
                    project_id.company_id.id: {
                        'id': project_id.sudo().company_id.id,
                        'name': project_id.sudo().company_id.name,
                    },
                },
            },
        )
        if feedback.exists():
            session_info['open_task_action'] = feedback.action_open_feedbacks(feedback, project_id)
        return session_info


    ########################################################################################################################

    @http.route(['/my/feedback/readonly/<int:feedback_id>', '/my/feedback/readonly/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_feedback_readonly(self, feedback_id=False, page=1, **kw):
        values = self._prepare_portal_layout_values()
        feedback = request.env['project.feedback'].search([('id', '=', feedback_id)])

        values.update({
            'feedback_id': feedback,
            'page_name': 'feedbacks',
            'default_url': '/my/feedback',
        })
        return request.render('cap_project_feedback_web.portal_my_feedback_readonly', values)


class FeedbackSharingChatter(PortalChatter):
    def _check_feedback_access_and_get_token(self, project_id, res_model, res_id, token):

        project_sudo = FeedbackWebsite._document_check_access(self, 'project.project', project_id, token)

        can_access = project_sudo and res_model == 'project.feedback' and project_sudo.with_user(SUPERUSER_ID)._check_project_sharing_access()
        session = None
        if can_access:
            session = request.env['project.feedback'].sudo().search(
                [('id', '=', res_id), ('project_id', '=', project_sudo.id)])
        if not can_access or not session:
            raise Forbidden()
        return session[session._mail_post_token_field]


    @route()
    def portal_chatter_init(self, thread_model, thread_id, **kwargs):
        feedback_id = request.env['project.feedback'].sudo().browse(thread_id)
        # replaced an inefficient "in search([])" membership check with .exists()
        if feedback_id.exists():
            project_sharing_id = feedback_id.project_id.id
            if project_sharing_id:
                token = self._check_feedback_access_and_get_token(project_sharing_id, thread_model, thread_id,
                                                                 kwargs.get('token'))
                if token:
                    del project_sharing_id
                    kwargs['token'] = token
        return super().portal_chatter_init(thread_model, thread_id, **kwargs)

    @http.route('/mail/chatter_fetch', type='json', auth='public', website=True)
    def portal_message_fetch(self, thread_model, thread_id, limit=10, after=None, before=None, **kw):
        if thread_model == 'project.feedback':
            feedback_id = request.env['project.feedback'].sudo().browse(thread_id)
            kw['token'] = feedback_id.project_id.sudo().access_token
            # replaced an inefficient "in search([])" membership check with .exists()
            if feedback_id.exists():
                project_sharing_id = feedback_id.project_id.id
                if project_sharing_id:
                    token = self._check_feedback_access_and_get_token(project_sharing_id, thread_model, thread_id,
                                                                      kw.get('token'))
                    if token is not None:
                        kw['token'] = token
        return super().portal_message_fetch(thread_model, thread_id, limit, after, before, **kw)