# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class ProductProduct_Photo(orm.Model):
    ''' Add extra field in product for sale purpose
    '''
    _inherit = 'product.product'

    def get_quotation_image(self, cr, uid, item, context=None):
        ''' Get single image for the file
            (default path is ~/photo/db_name/quotation
        '''        
        img = ''         
        extension = "jpg"
        image_path = os.path.expanduser(
            "~/photo/%s/product/default" % cr.dbname)
        _logger.warning('Search image: %s' % image_path)
        empty_image= "%s/%s.%s" % (
            image_path, 
            "empty", 
            extension)

        product_browse=self.browse(cr, uid, item, context=context)
        # Image compoesed with code format (code.jpg)
        if product_browse.default_code:
            try:
                (filename, header) = urllib.urlretrieve(
                    "%s/%s.%s" % (
                        image_path, 
                        product_browse.default_code.replace(" ", "_"), 
                        extension)) # code image
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
                _logger.warning(filename)
            except:
                img = ''
            
            if not img: # empty image:
                try:
                    (filename, header) = urllib.urlretrieve(empty_image)
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''
        return img

    # Fields function:
    def _get_quotation_image(self, cr, uid, ids, field_name, arg, 
            context=None):
        ''' Field function, for every ids test if there's image and return
            base64 format according to code value (images are jpg)
        '''
        res = {}
        for item in ids:
            res[item] = self.get_quotation_image(cr, uid, item, 
                context=context)
        return res                

    _columns = {
        # TODO remove? not used used default_photo in external module
        'quotation_photo': fields.function( # Second company
            _get_quotation_image, type="binary", method=True),

        'telaio': fields.char('Telaio', size=64, translate=True),
        'pipe_diameter': fields.char(
            'Diam. tubo', size=15),
        'weight_packaging': fields.char('Peso imballo', size=20),
        'item_per_box': fields.char('Pezzi per scatola', size=20),
        'item_per_pallet': fields.char('Pezzi per bancale', size=20),
        'item_per_mq': fields.char('Pezzi per metro cubo', size=20),
        'item_per_camion': fields.char('Pezzi per camion 13,6 mt.', size=20),
        'extra_description': fields.text('Extra description', translate=True),
        # Non visibili attualmente nella vista
        'dim_article': fields.char('Dim. art.', size=20),
        'dim_pack': fields.char('Dim. scatola', size=20),
        'dim_pallet': fields.char('Dim. pallet', size=20),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
