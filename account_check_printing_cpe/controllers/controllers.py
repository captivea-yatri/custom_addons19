# -*- coding: utf-8 -*-
from odoo import http

# class AccountCheckPrintingCpe(http.Controller):
#     @http.route('/account_check_printing_cpe/account_check_printing_cpe/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_check_printing_cpe/account_check_printing_cpe/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_check_printing_cpe.listing', {
#             'root': '/account_check_printing_cpe/account_check_printing_cpe',
#             'objects': http.request.env['account_check_printing_cpe.account_check_printing_cpe'].search([]),
#         })

#     @http.route('/account_check_printing_cpe/account_check_printing_cpe/objects/<model("account_check_printing_cpe.account_check_printing_cpe"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_check_printing_cpe.object', {
#             'object': obj
#         })