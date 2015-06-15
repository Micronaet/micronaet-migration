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
            input_file="~/ETL/pricelist.csv", delimiter=";", 
            header_line = 0, context=None):
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
        
        # NOTE: There's another procedure that delete only partner imported 
        # pricelist, see if it's better do this

        # ---------------------------------------------------------------------
        # Start pricelist importation from price exception in partner:
        # ---------------------------------------------------------------------
        # TODO check: 
        type_ids = self.pool.get('product.pricelist.type').search(cr, uid, [
            ('key', '=', 'sale')], context=context)
            
        #TODO cur_EUR=getCurrency(sock,dbname,uid,pwd,'EUR')
        #cur_CHF=getCurrency(sock,dbname,uid,pwd,'CHF')

        csv_file = open(os.path.expanduser(input_file), 'rb')
        lines = csv.reader(csv_file, delimiter=separator)
        counter = {
            'tot': -header_lines,
            'new': 0,
            'upd': 0,
            } 

        try:
            for line in lines:
                if counter['tot'] < 0:  # jump n lines of header 
                   counter['tot'] += 1
                else:
                    if len(line): # jump empty lines
                       counter['tot'] += 1 
                       default_code = Prepare(line[0]) 
                       # TODO migrate prepare function in a module csv_base
         
                       data = {
                           'name': name,
                           'mexal_id': default_code,
                           }
                       
                       item_ids = self.pool.get('product.product').search(
                           cr, uid, [('default_code', '=', default_code)])
                       # TODO arrivato qui! ***********************************    
                       if item_ids: # update
                          try:
                              article_mod = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data) 
                          except:
                              print "[ERROR] Modify product, current record:", data
                              raise 
                          print "[INFO]", counter['tot'], "Already exist: ", ref, name
                       else:           
                          counter['new'] += 1  
                          error="Creating product"
                          try:
                              article_new=sock.execute(dbname, uid, pwd, 'product.product', 'create', data) 
                          except:
                              print "[ERROR] Create product, current record:", data
                              raise                
                          print "[INFO]",counter['tot'], "Insert: ", ref, name
              
        except:
            print '>>> [ERROR] Error importing articles!'
            raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

        print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"        
                return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
