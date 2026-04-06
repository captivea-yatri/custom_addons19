# -*- coding: utf-8 -*-
from odoo import http

class CoEfficientInventory(http.Controller):
     @http.route('/co_efficient_inventory/co_efficient_inventory/', auth='public')
     def index(self, **kw):
         return "Hello, world"

     @http.route('/co_efficient_inventory/co_efficient_inventory/objects/', auth='public')
     def list(self, **kw):
         return http.request.render('co_efficient_inventory.listing', {
             'root': '/co_efficient_inventory/co_efficient_inventory',
             'objects': http.request.env['co_efficient_inventory.co_efficient_inventory'].search([]),
         })

     @http.route('/co_efficient_inventory/co_efficient_inventory/objects/<model("co_efficient_inventory.co_efficient_inventory"):obj>/', auth='public')
     def object(self, obj, **kw):
         return http.request.render('co_efficient_inventory.object', {
             'object': obj
         })