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
import base64
import urllib
from openerp import tools
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

class ProductProductPurchase(orm.Model):
    _inherit = 'product.product'

    def get_quotation_image(self, cr, uid, item, context=None):
        ''' Get single image for the file
            (default path is ~/photo/db_name/quotation
        '''
        img = ''
        try:
            extension = "jpg"
            image_path = os.path.expanduser(
                "~/photo/%s/product/quotation" % cr.dbname)
            empty_image= "%s/%s.%s" % (image_path, "empty", extension)

            product_browse = self.browse(cr, uid, item, context=context)
            # Image compoesed with code format (code.jpg)
            if product_browse.default_code:
                (filename, header) = urllib.urlretrieve(
                    "%s/%s.%s" % (
                        image_path,
                        product_browse.default_code.replace(" ", "_"),
                        extension)) # code image
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()

                if not img: # empty image:
                    (filename, header) = urllib.urlretrieve(empty_image)
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
        except:
            try:
                print (
                    "Image error", product_browse.default_code, sys.exc_info())
            except:
                pass
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
            res[item] = self.get_quotation_image(
                cr, uid, item, context=context)
        return res

    _columns = {
        'quotation_photo':fields.function(
            _get_quotation_image, type="binary", method=True),
        'quantity_x_pack': fields.integer('Q. per pack'),

        'colls_number': fields.integer('Colli'),
        'colls': fields.char('Colli', size=30),

        'colour_code': fields.char('Codice colore', size=64),

        'default_supplier': fields.char('Fornitore default', size=64),
        'default_supplier_code': fields.char('Codice forn. default', size=40),

        'pack_l': fields.float('L. Imb.', digits=(16, 2)),
        'pack_h': fields.float('H. Imb.', digits=(16, 2)),
        'pack_p': fields.float('P. Imb.', digits=(16, 2)),
        }

    _defaults = {
        'quantity_x_pack': lambda *a: 1,
        }

class purchase_order_extra(orm.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'q_x_pack': fields.related(
            'product_id', 'q_x_pack', type='integer', string='Package'),
        'colour': fields.related(
            'product_id', 'colour', type='char', size=64, string='Color'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
