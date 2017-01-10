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

class ResCompany(orm.Model):
    """ Model name: ResCompany
    """
    _inherit = 'res.company'

    def history_previous_year_net(self, cr, uid, ids, context=None):
        ''' Call procedure in product obj
        ''' 
        return self.pool.get('product.product').history_previous_year_net(
            cr, uid, False, context=context)


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'
    
    def history_previous_year_net(self, cr, uid, ids, context=None):
        ''' History previous data for new management
        '''
        if context is None:
            context = {}
            
        product_ids = self.search(cr, uid, [], context=context)
        ctx = context.copy()
        ctx['limit_up_date'] = '2016-12-31 23:59:59' # set limit
        
        for product in self.browse(
                cr, uid, product_ids, context=ctx):
            self.write(cr, uid, product.id, {
                'mx_history_net_qty': product.mx_net_qty,
                }, context=ctx)
        
        return True
        
    _columns = {
        'mx_history_net_qty': fields.float('History net', digits=(16, 2)),
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
