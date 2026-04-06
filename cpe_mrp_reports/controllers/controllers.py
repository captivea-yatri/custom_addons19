# -*- coding: utf-8 -*-

from odoo import http
import pdb


class CpeMrpReports(http.Controller):

    @http.route('/cpe/mrp/report/<int:cpe_mrp_report_id>', type='http', auth='user', website=True)
    def mrp_report_cost_review(self, cpe_mrp_report_id, **kwargs):
        '''This controller route handles HTTP requests for generating MRP cost review reports based on provided report ID and function parameter.
        It retrieves the relevant report object, extracts the associated resource IDs, and dynamically invokes the specified function on those resources, returning the result.'''
        report_id = http.request.env['cpe.mrp.report'].browse([cpe_mrp_report_id])
        function = kwargs.get('function')
        if report_id and function:
            rec_ids = [int(x) for x in report_id.res_ids.split(",")]
            rec = http.request.env[report_id.res_model].browse(rec_ids)
            return getattr(rec, function)()

