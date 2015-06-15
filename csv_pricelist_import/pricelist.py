# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

class ProductPricelist(orm.Model):
    ''' Add scheduled operations
    '''
    _inherit = 'product.pricelist'
    
    def schedule_csv_pricelist_import(self, cr, uid, 
            input_file="~/ETL/artioerp.csv", delimiter=";", 
            header_line=0, context=None):
        ''' Import pricelist and setup particular price for partners
            (the partners are imported with SQL methods)
            
            This importation is generated from product csv file for standard
            pricelist, remember that there are also partner pricelist with
            particular price (not imported here)
            
            Note: pricelist yet present here (only item are unlink / create)
        '''
        csv_pool = self.pool.get('csv.base')
        item_pool = self.pool.get('product.pricelist.item')
        version_pool = self.pool.get('product.pricelist.version')
        product_pool = self.pool.get('product.product')

        _logger.info("Start pricelist standard importation")
                
        # Erase all pricelist item (only) before import:
        item_ids = item_pool.search(cr, uid, [], context=context)
        item_pool.unlink(cr, uid, item_ids, context=context)

        # Load standard pricelist version:
        versions = {}
        version_ids = version_pool.search(cr, uid, [
            ('mexal_id', 'in', range(1, 10))], context=context)            
        for item in version_pool.browse(cr, uid, version_ids, context=context):
            versions[item.mexal_id] = item.id

        csv_file = open(os.path.expanduser(input_file), 'rb')
        lines = csv.reader(csv_file, delimiter=separator)
        counter = -header_line

        price_list = {} # dict for save product prices
        try:
            for line in lines:
                if counter['tot'] < 0:  # jump n lines of header 
                   counter['tot'] += 1
                else:
                    if not len(line): # jump empty lines
                        continue
                        
                    counter['tot'] += 1
                    default_code = csv_pool.decode_string(line[0])
                    name = csv_pool.decode_string(line[1]).title()                     
                    
                    # NOTE: load only this pricelist (not all 10)
                    price_list[1] = csv_pool.decode_float(line[6])
                    price_list[4] = csv_pool.decode_float(line[7])
                    price_list[5] = csv_pool.decode_float(line[8])
                    price_list[6] = csv_pool.decode_float(line[9])
                    
                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                if not product_ids: 
                    _logger.error("Product not found %s" % default_code)
                    continue # jump (not created here)                    
                elif len(product_ids) > 1: 
                    _logger.warning("Multiple product %s" % default_code)
                    continue # jump
                    
                for pl in price_list:
                    if price_list[pl]: 
                        item_pool.create(cr, uid, {
                            'price_version_id': versions[pl],
                            'sequence': 10,
                            'name': '%s [%s]' % (name, ref),
                            'base': 2, #1 pl 2 cost
                            'min_quantity': 1,
                            'product_id': product_ids[0],
                            'price_discount': -1,
                            'price_surcharge': price_list[pl],
                            'price_round': 0.01,                          
                            }, context=context)
                    
        except:
            _logger.error("Pricelist import %s" % (sys.exc_info(), ))
            return False

        _logger.info(
            "Pricelist imported [%(tot)s] - new %(new)s upd %(upd)s" % counter)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
