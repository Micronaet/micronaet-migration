# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import sys
import logging
import openerp
import base64
import urllib
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp import tools  # for parameters
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)

class ProductQuotationFolder(osv.osv):
    _name = 'product.quotation.folder'

    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'addons': fields.boolean('Addons root path', required=False,
            help="Start from addons path, extra path is append to addons "
                "folder, instead of extra is complete path"),
        'root_path': fields.char('Folder extra path', size=128,required=False,
            help="Path extra default root folder, ex.: http://server/openerp"),
        'folder_path': fields.char('Folder extra path', size=128,
            required=True,
            help="Path extra default root folder, ex.: thumb/400/color, or "
                "complete path: /home/admin/photo"),
        'extension_image': fields.char('Extension', size=15, required=True,
            help="without dot, for ex.: jpg"),
        'default': fields.boolean('Default'),
        'width': fields.integer('Witdh in px.'),
        'height': fields.integer('Height in px.'),
        'empty_image': fields.char('Empty image', size=64, required=True,
            help="Complete name + ext. of empty image, ex.: 0.png"),
        }

    _defaults = {
        'default': lambda *x: False,
        }

class ProductProductImage(osv.osv):
    ''' Add extra function and fields for manage picture for product
    '''
    _inherit = 'product.product'

    def get_image(self, cr, uid, item, context=None):
        ''' Get folder (actually 200 px) and extension from folder obj.
            Calculated dinamically image from module
            image folder + extra path + ext.
            Return image
        '''
        # TODO Better rewrite all this mess function!
        with_log = True # TODO debug part
        img = ''
        folder_proxy = self.pool.get('product.quotation.folder')
        folder_ids = folder_proxy.search(cr, uid, [('width', '=', 200)])

        if folder_ids:
           folder_browse = folder_proxy.browse(cr, uid, folder_ids)[0]
           extension = "." + folder_browse.extension_image
           empty_image = folder_browse.empty_image
           if folder_browse.addons:
              image_path = tools.config[
                  'addons_path'] + '/quotation_photo/images/' + \
                  folder_browse.folder_path + "/"
           else:
              image_path = os.path.expanduser(
                  (folder_browse.folder_path + "/") % (cr.dbname, )
                      if len(folder_browse.folder_path.split("%s")) == 2
                      else folder_browse.folder_path + "/")
        else: # no folder image
           return img # empty!

        product_browse = self.browse(cr, uid, item, context=context)
        code = product_browse.code
        if code:
            # codice originale (tutte le cifre)
            try:
                (filename, header) = urllib.urlretrieve(
                    image_path + code.replace(
                        " ", "_") + extension) # code image
                f = open(filename , 'rb')
                if with_log:
                    _logger.info('>> Load image: %s' % filename) # TODO debug

                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''

            # codice padre (con spazi):
            if not img and code:
                try:
                    (filename, header) = urllib.urlretrieve(
                        image_path + code + extension) # code image
                    f = open(filename , 'rb')
                    if with_log:
                        _logger.info('>> Load image: %s' % filename) # TODO debug
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''

            # codice padre (5 cifre):
            if (not img) and code and len(code) >= 5:
                try:
                    padre = code[:5]
                    (filename, header) = urllib.urlretrieve(
                        image_path + padre.replace(" ", "_") + extension)
                    f = open(filename , 'rb')
                    if with_log:
                        _logger.info('>> Load image: %s' % filename) # TODO debug
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''

            # codice padre (3 cifre):
            if not img and code and len(code) >= 3:
                try:
                    padre = product_browse.code[:3]
                    (filename, header) = urllib.urlretrieve(
                        image_path + padre.replace(" ", "_") + extension)
                    f = open(filename , 'rb')
                    if with_log:
                        _logger.info('>> Load image: %s' % filename) # TODO debug
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''

            # Empty image (default or empty in module):
            if not img:
                try:
                    (filename, header) = urllib.urlretrieve(
                        image_path + empty_image) # empty setted up on folder
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    (filename, header) = urllib.urlretrieve(tools.config[
                        'addons_path'] + '/quotation_photo/empty.png')
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                    #img = ''
        return img

    def _get_image(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        #_logger.warning('Loading image for product: %s' % (ids, )) # TODO debug
        for item in ids:
            res[item] = self.get_image(cr, uid, item, context=context)
        return res

    _columns = {
        'default_photo': fields.function(_get_image, type="binary", 
            method=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
