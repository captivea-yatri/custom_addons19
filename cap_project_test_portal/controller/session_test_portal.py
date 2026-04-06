from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo import  http, _
from odoo.exceptions import AccessError, MissingError


class SessionTestPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """
        This method is used to return session menu with count list of session test
        """
        values = super()._prepare_home_portal_values(counters)
        if 'session_count' in counters:
            project_ids = request.env['project.project'].search([]) \
                if request.env['project.project'].has_access('read') else 0
            values['session_count'] = request.env['session.test'].sudo().search_count(
                [('project_id', 'in', project_ids.ids)])
        return values

    # def _prepare_session_test_domain(self, project_ids):
    #     return [('project_id', 'in', project_ids.ids)]

    # def _prepare_searchbar_sortings(self):
    #     return {
    #         'date': {'label': _('Newest'), 'order': 'create_date desc'},
    #         'name': {'label': _('Name'), 'order': 'name'},
    #     }

    @http.route(['/my/project_tests', '/my/project_tests/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_project_tests(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """
        This method is used to create page of portal and render the template
        """
        values = self._prepare_portal_layout_values()
        Project = request.env['project.project']
        domain = self._prepare_project_domain()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name asc'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # projects count
        project_count = Project.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/project_tests",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=project_count,
            page=page,
            step=self._items_per_page
        )

        # content according to pager and archive selected
        projects = Project.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_projects_history'] = projects.ids[:100]

        values.update({
            'date': date_begin,
            'date_end': date_end,
            'projects': projects,
            'page_name': 'project tests',
            'default_url': '/my/project_tests',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby
        })
        return request.render("cap_project_test_portal.portal_my_project_tests", values)

    @http.route(['/my/project_tests/<int:project_id>', '/my/project_tests/<int:project_id>/page/<int:page>'],
                type='http',
                auth="public", website=True)
    def portal_my_session(self, project_id=None, access_token=None):
        session_test_ids = request.env['session.test'].search([('project_id', '=', project_id)])
        try:
            self._document_check_access('project.project', project_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        # if project_sudo and project_sudo.with_user(request.env.user)._check_project_sharing_access():
        values = {'project_id': project_id}
        if session_test_ids:
            values['session_test_ids'] = session_test_ids
        return request.render("cap_project_test_portal.project_test_session_sharing_portal", values)

    @http.route("/my/sessions/<int:project_id>/session_sharing", type="http", auth="user", website=True,
                methods=['GET'])
    def render_session_test_backend_view(self, project_id):
        """
        This method is used to find the session test and render the template of session test embed based on session test
        """
        session_test_ids = request.env['session.test'].search([('project_id', '=', project_id)])
        session_info = self._prepare_session_test_info(session_test_ids, project_id)
        if not session_info:
            return request.redirect('/my')
        return request.render(
            'cap_project_test_portal.session_test_embed',
            {'session_info': session_info},
        )

    def _prepare_session_test_info(self, session_test, project_id):
        """
        This method is used to prepare session value and pass the backend tree view session test action to session
        """
        project_test_id = request.env['project.project'].browse(project_id)
        session_info = request.env['ir.http'].sudo().session_info()
        user_context = dict(request.env.context) if request.session.uid else {}
        mods = conf.server_wide_modules or []
        if request.env.lang:
            lang = request.env.lang
            session_info['user_context']['lang'] = lang
            # Update Cache
            user_context['lang'] = lang
        session_info['user_context']['is_created_from_website'] = True
        user_context['is_created_from_website'] = True
        lang = user_context.get("lang")
        translation_hash = request.env['ir.http'].get_web_translations_hash(mods, lang)
        cache_hashes = {
            "translations": translation_hash,
        }
        session_info.update(
            cache_hashes=cache_hashes,
            action_name=session_test.action_open_session_test(session_test, project_test_id),
            # FIXME: See if we prefer to give only the currency that the portal user just need to see the correct information in project sharing
            currencies=request.env['ir.http'].get_currencies(),
            user_companies={
                'current_company': project_test_id.sudo().company_id.id,
                'allowed_companies': {
                    project_test_id.company_id.id: {
                        'id': project_test_id.sudo().company_id.id,
                        'name': project_test_id.sudo().company_id.name,
                    },
                },
            },
        )

        if session_test:
            session_info['open_task_action'] = session_test.action_open_session_test(session_test, project_test_id)
        return session_info

    #     controller for launch session form view

    @http.route(['/my/test/<int:session_id>', '/my/test/<int:session_id>/page/<int:page>'],
                type='http',
                auth="public", website=True)
    def portal_my_session_launch(self, session_id=None, access_token=None):
        """
        This method is used to render the template of session test launch
        """
        record = request.env['session.test'].sudo().browse(session_id)
        # Update status from "sent" → "in_progress"
        if record and record.status == 'sent' and record.assigned_user_id.id == request.env.user.id:
            record.sudo().write({'status': 'in progress'})
            
        values = {'session_id': session_id}
        return request.render("cap_project_test_portal.project_test_session_launch_sharing_portal", values)
        # session_test_id = request.env['session.test'].browse(session_id)
        # try:
        #     project_sudo = self._document_check_access('project.project', session_test_id.project_id.id, access_token)
        # except (AccessError, MissingError):
        #     return request.redirect('/my')
        # if project_sudo and project_sudo.with_user(request.env.user)._check_project_sharing_access():
        #     values = {'project_id': session_test_id.project_id}
        #     if session_test_id:
        #         values['session_id'] = session_id
        #     return request.render("cap_project_test_portal.project_test_session_launch_sharing_portal", values)

    @http.route("/my/sessions_launch/<int:session_id>/session_sharing", type="http", auth="user", website=True,
                methods=['GET'])
    def render_session_test_launch_backend_view(self, session_id):
        """
        This method is used to find the session test launch and render the template of session test launch embed based on session test
        """
        session_test_id = request.env['session.test'].browse(session_id)
        return request.render(
            'cap_project_test_portal.session_test_embed',
            {'session_info': self._prepare_session_test_launch_info(session_test_id), 'id': session_test_id.id},
        )

    def _prepare_session_test_launch_info(self, session_test_id):
        """
        This method is used to prepare session test launch value and pass the backend tree view session test launch action to session
        """
        project_test_id = request.env['project.project'].sudo().browse(session_test_id.sudo().project_id.id)
        session_info = request.env['ir.http'].sudo().session_info()
        user_context = dict(request.env.context) if request.session.uid else {}
        mods = conf.server_wide_modules or []
        if request.env.lang:
            lang = request.env.lang
            session_info['user_context']['lang'] = lang
            # Update Cache
            user_context['lang'] = lang
        lang = user_context.get("lang")
        translation_hash = request.env['ir.http'].get_web_translations_hash(mods, lang)
        cache_hashes = {
            "translations": translation_hash,
        }
        session_info.update(
            cache_hashes=cache_hashes,
            action_name=session_test_id.action_open_session_test_launch(project_test_id),
            # FIXME: See if we prefer to give only the currency that the portal user just need to see the correct information in project sharing
            currencies=request.env['ir.http'].get_currencies(),
            user_companies={
                'current_company': project_test_id.company_id.id,
                'allowed_companies': {
                    project_test_id.company_id.id: {
                        'id': project_test_id.company_id.id,
                        'name': project_test_id.company_id.name,
                    },
                },
            },
        )
        if session_test_id:
            session_info['open_task_action'] = session_test_id.action_open_session_test_launch(project_test_id)
        return session_info

    @http.route(['/my/back_to_edit/<int:session_id>'], type="http", auth="user", website=True,
                methods=['GET'])
    def portal_back_to_edit_mode(self, session_id, **kwargs):
        session_test_id = request.env['session.test'].browse(session_id)
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action = request.env["ir.actions.actions"]._for_xml_id("cap_project_test.action_session_test").get('id')
        menu_id = request.env.ref('cap_project_test.session_test_sub_menu').id
        session_test_id.backend_url = """{}/web#id={}&cids=10&menu_id={}&action={}&model=session.test&view_type=form""".format(
            base_url, session_test_id.id, menu_id, action)
        return request.redirect(session_test_id.backend_url)
