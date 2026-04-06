# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class ProductCurrency(http.Controller):
    @http.route('/product_currency/product_currency/', auth='public')
    def index(self, **kw):
        """
                Handle HTTP GET requests to the route '/product_currency/product_currency/'.

                Returns:
                    str: A simple string response, "Hello, world".
                """
        return "Hello, world"

    @http.route('/product_currency/product_currency/objects/', auth='public')
    def list(self, **kw):
        """
           Handle HTTP GET requests to the route '/product_currency/product_currency/objects/'.

           Returns:
               werkzeug.wrappers.Response: A response rendered using a template called 'product_currency.listing'.
           """
        return http.request.render('product_currency.listing', {
            'root': '/product_currency/product_currency',
            'objects': http.request.env['product_currency.product_currency'].search([]),
        })

    @http.route('/product_currency/product_currency/objects/<model("product_currency.product_currency"):obj>/',
                auth='public')
    def object(self, obj, **kw):
        """
           Handle HTTP GET requests to the route '/product_currency/product_currency/objects/<model("product_currency.product_currency"):obj>/'.

           Returns:
               werkzeug.wrappers.Response: A response rendered using a template called 'product_currency.object'.
           """
        return http.request.render('product_currency.object', {
            'object': obj
        })


class ProductCurrencyPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super(ProductCurrencyPortal, self)._prepare_home_portal_values(counters)
        values['currency_counts'] = request.env['product_currency.product_currency'].search_count([])
        return values

    @http.route(['/product_currency/product_currency/objects/'], type='http', website=True)
    def weblearnscurrencyListView(self, **kw):
        currency_obj = request.env['product_currency.product_currency']
        currency = currency_obj.search([])
        vals = {'currency': currency, 'page_name': 'currency_list_view'}
        return request.render("product_currency.currency_list_view", vals)

    @http.route(['/product_currency/product_currency/objects/<model("product_currency.product_currency"):currency_id>'],
                type="http", website=True)
    def weblearnscurrencyFormView(self, currency_id, **kw):
        vals = {"currency": currency_id, 'page_name': 'currency_form_view'}
        return request.render("product_currency.currency_form_view", vals)
