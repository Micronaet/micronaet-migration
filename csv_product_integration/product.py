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
import csv
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

class ProductProduct(orm.Model):
    ''' Add scheduled operations
    '''
    _inherit = 'product.product'
            
    def schedule_csv_product_integration(self, cr, uid, 
            input_file="~/ETL/artioerp.csv", delimiter=";", header_line=0,
            verbose=100, context=None):
        ''' Import product extra fields, this operation override sql schedule
            for add extra fields that could not be reached fast
        '''       
        
        _logger.info("Start product integration")

        csv_pool = self.pool.get('csv.base')
        csv_file = open(os.path.expanduser(input_file), 'rb')
        counter = -header_line
        try:
            for line in csv.reader(csv_file, delimiter=delimiter):
                if counter < 0:  # jump n lines of header 
                    counter += 1
                    continue
                   
                if not len(line): # jump empty lines
                    continue

                if verbose and counter % verbose == 0:
                    _logger.info("Product integrated: %s" % counter)
                counter += 1
                default_code = csv_pool.decode_string(line[0])
                    
                product_ids = self.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                    
        except:
            _logger.error("Product integration %s" % (sys.exc_info(), ))
            return False

            
        _logger.info("End product integration!")
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
