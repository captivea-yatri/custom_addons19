# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class ProductPurchase(http.Controller):
    @http.route('/product_purchase/product_purchase/', auth='public')
    def index(self, **kw):
        """
            Handle HTTP GET requests to the route '/product_purchase/product_purchase/'.

                    Returns:
                        str: A simple string response, "Hello, world".
                    """
        return "Hello, world"

    @http.route('/product_purchase/product_purchase/objects/', auth='public')
    def list(self, **kw):
        """
           Handle HTTP GET requests to the route '/product_purchase/product_purchase/objects/'.

           Returns:
               werkzeug.wrappers.Response: A response rendered using a template called 'product_purchase.listing'.
           """
        return http.request.render('product_purchase.listing', {
            'root': '/product_purchase/product_purchase',
            'objects': http.request.env['product_purchase.product_purchase'].search([]),
        })

    @http.route('/product_purchase/product_purchase/objects/<model("product_purchase.product_purchase"):obj>/',
                auth='public')
    def object(self, obj, **kw):
        """
           Handle HTTP GET requests to the route '/product_purchase/product_purchase/objects/<model("product_purchase.product_purchase"):obj>/'.

           Returns:
               werkzeug.wrappers.Response: A response rendered using a template called 'product_purchase.object'.
           """
        return http.request.render('product_purchase.object', {
            'object': obj
        })


class ProductPurchasePortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super(ProductPurchasePortal, self)._prepare_home_portal_values(counters)
        values['product_counts'] = request.env['product_purchase.product_purchase'].search_count([])
        return values

    @http.route(['/product_purchase/product_purchase/objects/'], type='http', website=True)
    def weblearnspurchaseListView(self, **kw):
        purchase_obj = request.env['product_purchase.product_purchase']
        purchase = purchase_obj.search([])
        vals = {'purchase': purchase, 'page_name': 'purchase_list_view'}
        return request.render("product_purchase.purchase_list_view", vals)

    @http.route(['/product_purchase/product_purchase/objects/<model("product_purchase.product_purchase"):purchase_id>'], type="http", website=True)
    def weblearnsCouponFormView(self, purchase_id, **kw):
        vals = {"purchase": purchase_id, 'page_name': 'purchase_form_view'}
        return request.render("product_purchase.purchase_form_view", vals)
