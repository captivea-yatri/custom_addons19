# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import config
import uuid
import shutil
import os
from shutil import copyfile
import pdb

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _production_has_attachments(self):
        '''
               Assigning value to the bom_has_attachments if the lines has any attachment or the related child bom lines have any attachment
               '''
        for production in self:
            try:
                production.production_has_attachments = bool(production.move_raw_ids.filtered(lambda line: bool(self.env['ir.attachment'].search([('res_model','=','product.template'),('res_id','=',line.product_id.product_tmpl_id.id)]))))
            except:
                pass

    production_has_attachments = fields.Boolean(compute="_production_has_attachments")

    def download_production_attachments(self):
        '''
        Method is called to trigger downloading process of attachments with fetching attachment, finiding source path and deciding target path as well as file name
        '''
        product_ids = self.move_raw_ids.filtered(lambda line: bool(self.env['ir.attachment'].search([('res_model','=','product.template'),('res_id','=',line.product_id.product_tmpl_id.id)]))).mapped('product_id').mapped('product_tmpl_id')
        if product_ids:
            fnames = []
            attachment_ids = self.env['ir.attachment'].search([('res_model','=','product.template'),('res_id','in',product_ids.ids)])
            archive_dir = "/tmp/" + str(uuid.uuid4()).replace("-","")[:10]
            os.mkdir( archive_dir )
            from_dir = config['data_dir'] + "/filestore/{}/".format(self.env.cr.dbname) + "{}"
            for attachment in attachment_ids:
                fname = attachment.name.replace("/","-")
                if fname in fnames:
                    fname = fname + str( len( filter(lambda filename: filename == fname, fnames) ) + 1 )
                fnames.append(fname)
                fromfpath = from_dir.format(attachment.store_fname)
                tofpath = archive_dir + "/{}".format(fname)
                try:
                    copyfile(fromfpath, tofpath)
                except FileNotFoundError:
                    pass
            shutil.make_archive(archive_dir, 'zip', archive_dir)             
            shutil.rmtree(archive_dir)
            return {
                'type': 'ir.actions.act_url',
                'url': '/mrp/download?path={}.zip'.format(archive_dir),
                'target': 'new'    
            }
