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

class CsvBase(orm.Model):
    ''' Add common function without fields/table
    '''
    _name = 'csv.base'
    _description = 'Base function'
    
    def get_create_partner_lite(self, cr, uid, ref, record=None, customer=True, 
            context=None):
        ''' Search a partner with accounting code
            If not present create one partner with a lite record
        '''
        partner_pool = self.pool.get('res.partner')
        if customer:
            key = 'sql_customer_code'
        else:    
            key = 'sql_supplier_code'            
            
        partner_ids = partner_pool.search(cr, uid, [
            (key, '=', ref)], context=context)
        if partner_ids:
            return partner_ids[0]
        if record is None:
            record = {
                'name': 'Partner %s' % ref,
                key: ref,                
                }          
        _logger.warning("Create a lite partner: %s" % (record, ))
        return partner_pool.create(cr, uid, record, context=context)        
        
    def decode_string(self, valore):  
        ''' Return string value of asc passed
        '''
        if not valore: 
            return ''
        valore = valore.decode('cp1252')
        valore = valore.encode('utf-8')
        return valore.strip()

    def decode_date(self, valore, with_slash=True):
        ''' Return date value of asc passed
        '''
        valore = valore.strip()
        if with_slash: # yet correct YYYY/MM/DD
            return valore or False
        else: # YYYYMMDD
            if len(valore) == 8:
                return "%s/%s/%s" % (
                    valore[:4], valore[4:6], valore[6:8])
        return False # when error


    def decode_float(self, valore):
        ''' Return float value of asc passed
        '''
        valore = valore.strip() 
        if valore: 
           return float(valore.replace(",", "."))
        else:
           return 0.0   # for empty values

    def decode_int(self, valore):
        ''' Return int value of asc passed
        '''
        valore = valore.strip() 
        if valore: 
           try:
               return int(valore)
           except:
               pass # next line:    
        return False   # for empty values
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
