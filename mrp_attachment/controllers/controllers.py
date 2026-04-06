# -*- coding: utf-8 -*-
from odoo import http
from werkzeug.wrappers import Response
import os

zip_headers = {
   'Content-type': 'application/octet-stream',
}

class MrpAttachment(http.Controller):
    # This controller calls when downlaoding attachment with required data
    @http.route('/mrp/download', auth='user', website=True)
    def download_attachment(self, **kw):
        path = kw.get('path')
        fname = path.split("/")[-1]
        fo = open(path,"rb")
        content = fo.read()
        fo.close()
        os.remove(path)
        zip_headers['Content-Disposition'] = 'attachment; filename={}'.format(fname)
        zip_headers['Content-Length'] = len(content)
        return Response(content,headers=zip_headers)
