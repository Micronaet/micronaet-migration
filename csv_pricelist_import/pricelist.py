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
    
    def schedule_csv_pricelist_import(self, cr, uid, context=None):
        ''' Import pricelist and setup particular price for partners
            (the partners are imported with SQL methods)
        '''
        # Erare all pricelist before import:
        item_pool = self.pool.get('product.pricelist.item')
        version_pool = self.pool.get('product.pricelist.version')
        
        item_ids = item_pool.search(cr, uid, [], context=context)
        item_pool.unlink(cr, uid, erase_ids, context=context)

        version_ids = version_pool.search(cr, uid, [], context=context)
        version_pool.unlink(cr, uid, version_ids, context=context)
        
        # Not delete pricelist because of pricelist setup (TODO integrate)    
        # First 10 are standard pricelist
        #pricelist_ids = self.search(cr, uid, [('id','>','10')], context=context)        
        #self.unlink(cr, uid, pricelist_ids, context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
