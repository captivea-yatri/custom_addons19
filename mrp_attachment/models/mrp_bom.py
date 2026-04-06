# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import config
import uuid
import shutil
import os
from shutil import copyfile
import pdb
import logging

_logger = logging.getLogger(__name__)

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _bom_has_attachments(self):
        '''
        Assigning value to bom_has_attachments field , if product on the lines have any attachment or related child bom lines have any attachment
        '''
        for bom in self:
            try:
                bom.bom_has_attachments = bool(bom.bom_line_ids.filtered(lambda line: line.attachments_count)) or bool(bom.bom_line_ids.mapped('child_bom_id').bom_line_ids.filtered(lambda line: line.attachments_count))
            except:
                pass

    bom_has_attachments = fields.Boolean(compute="_bom_has_attachments")

    def add_line_to_dir(self, line, path=None):
        '''
        Called from process_line()
        for bom lines having any attachment related to product template, this method is called and create file-name, fetch sourcepath and decide target path
        '''
        fnames = []
        product_id = line.product_id.product_tmpl_id
        attachment_ids = self.env['ir.attachment'].search([('res_model','=','product.template'),('res_id','=',product_id.id)])
        from_dir = config['data_dir'] + "/filestore/{}/".format(self.env.cr.dbname) + "{}"
        for attachment in attachment_ids:
            fname = attachment.name.replace("/","")
            if fname in fnames:
                infnames = [ x for x in fnames if x == fname ]
                fname = fname + str( len( infnames ) + 1 )
            fnames.append(fname)
            fromfpath = from_dir.format(attachment.store_fname)
            tofpath = path + "/{}".format(fname)
            try:
                copyfile(fromfpath, tofpath)
            except:
                pass

    def process_line(self, line, path=None):
        '''
        Called from add_bom_to_dir()
         If line already have attachement count(Product templaate have any attachment) or child bom's then it will be aaded to directory
         '''
        if line.attachments_count:
            self.add_line_to_dir( line, path=path)
        if line.child_bom_id:
            line.child_bom_id.add_bom_to_dir( path=path )

    def add_attachment_to_dir(self, attachment_id, from_dir=None, path=None):
        '''
        Called from add_product_attachments_to_dir()
        Search for the attachment via id provided and make copy of file from source location and pasting it into destination location
        '''
        attachment = self.env['ir.attachment'].browse([attachment_id])
        fname = attachment.name.replace("/","-")
        fromfpath = from_dir.format(attachment.store_fname)
        tofpath = path + "/{}".format(fname)
        try:
            copyfile(fromfpath, tofpath)
        except:
            pass

    def add_product_attachments_to_dir(self, path=None):
        '''
        Called from download_bom_attachments()
        Search for attachments related to product and calls method to add attachment to directory
        '''
        attachment_ids = self.env['ir.attachment'].search([('res_model','=','product.template'),('res_id','=',self.product_tmpl_id.id)])
        from_dir = config['data_dir'] + "/filestore/{}/".format(self.env.cr.dbname) + "{}"
        path += "/{}".format(self.product_tmpl_id.name.replace("/","-"))
        os.mkdir( path )
        for attachment in attachment_ids:
            self.add_attachment_to_dir( attachment.id, from_dir=from_dir, path=path)

    def add_bom_to_dir(self, path=None):
        '''
        Called from download_bom_attachments() and process_line()
        Returns the path for directory by triggering method which will either generate random 10 digit string which has prefix /tmp/ as path
        or if path is there then adds product record name at the end of it. For every line in bom_line it calls the method to check every line
        '''
        if not path:
            path = "/tmp/" + str(uuid.uuid4()).replace("-","")[:10]
            os.mkdir( path )
        else:
            path += "/{}".format(self.product_tmpl_id.name.replace("/","-"))
            os.mkdir( path )
        for line in self.bom_line_ids:
            self.process_line( line, path=path )
        return path

    def download_bom_attachments(self):
        '''
        Main method for downloading attachments , trigger different methods and in return downloads the directory with attachment
        '''
        path = self.add_bom_to_dir()
        self.add_product_attachments_to_dir( path=path)
        shutil.make_archive(path, 'zip', path)
        shutil.rmtree(path)
        return {
            'type': 'ir.actions.act_url',
            'url': '/mrp/download?path={}.zip'.format(path),
            'target': 'new'
        }
