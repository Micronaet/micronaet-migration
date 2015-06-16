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
        
        # Load UOM:
        uoms = {}   
        uom_failed = []                 
        uom_pool = self.pool.get('product.uom')
        uom_ids = uom_pool.search(cr, uid, []) # no context (english)
        for uom in uom_pool.browse(
                cr, uid, uom_ids, context=context):
            uoms[uom.name] = uom.id
        

        csv_pool = self.pool.get('csv.base')
        csv_file = open(os.path.expanduser(input_file), 'rb')
        counter = -header_line
        language = {}
        for line in csv.reader(csv_file, delimiter=delimiter):
            try:
                if counter < 0:  # jump n lines of header
                    counter += 1
                    continue

                if not len(line): # jump empty lines
                    continue

                if verbose and counter and counter % verbose == 0:
                    _logger.info("Product integrated: %s" % counter)
                counter += 1

                # CSV fields:
                default_code = csv_pool.decode_string(line[0])
                uom = csv_pool.decode_string(line[2]).upper()
                               
                # Language:
                #language['it_IT']:
                name = csv_pool.decode_string(line[1]).title()
                language['en_US'] = csv_pool.decode_string(line[10]).title()
                # TODO: activate language
                #language['1'] = csv_pool.decode_string(line[11]).title()
                #language['2'] = csv_pool.decode_string(line[12]).title()
                #language['3'] = csv_pool.decode_string(line[13]).title()

                try: # sale lot of product
                   lot = eval(csv_pool.decode_string(
                       line[5]).replace(',', '.'))
                except:
                   lot = 0

                # Anagraphic fields:
                linear_length = csv_pool.decode_float(line[14])
                volume = csv_pool.decode_float(line[15])
                weight = csv_pool.decode_float(line[16])

                # Sometimes not present:
                if len(line) > 18:
                    colour = csv_pool.decode_string(line[18])
                else:
                    colour = ""

                # Get UOM depend on ref:
                if uom in ['NR', 'N.', 'PZ', 'RT']: 
                    uom_id = uoms.get("Unit(s)", False)
                elif uom in ['M2', 'MQ']: 
                    uom_id = uoms.get('M2', False)
                elif uom in ['M', 'MT', 'ML',]: # NOTE: after M2!! 
                    uom_id = uoms.get('m', False)
                elif uom == 'HR': 
                    uom_id = uoms.get('Hour(s)', False)
                elif uom == 'KG': 
                    uom_id = uoms.get('kg', False)
                elif uom == 'LT': 
                    uom_id = uoms.get('Liter(s)', False)
                elif uom == 'KW': 
                    uom_id = uoms.get('KW', False)
                elif uom in ['M3', 'MC']: 
                    uom_id = uoms.get('M3', False)
                elif uom in ['PA', 'CO', 'CP']: 
                    uom_id = uoms.get('P2', False) #pair
                elif uom == 'PC': 
                    uom_id = uoms.get('P10', False)
                elif uom in ['', 'CN', 'MG', 'CM', 'CF', ]: # TODO ??
                    uom_id = uoms.get("Unit(s)", False)
                else: 
                    if uom not in uom_failed:
                        uom_failed.append(uom)
                    uom_id = uoms.get("Unit(s)", False)

                if not uom_id:
                    uom_id = uoms.get("Unit(s)", False)

                product_ids = self.search(cr, uid, [
                    ('default_code', '=', default_code)]) #, context=context)
                data = {
                    'linear_length': linear_length,
                    'weight': weight,
                    'volume': volume,
                    'colour': colour,
                    'q_x_pack': lot,
                    'description_sale': name,
                    'name_template': name, # TODO langs
                    #'name': name,

                    #'active': active,
                    #'mexal_id': ref,
                    #'import': True,
                    #'sale_ok': True,
                    #'purchase_ok': True,
                    #'default_code': ref,
                    #'type': 'product',
                    #'supply_method': 'produce',
                    #'standard_price': bug_start_value,
                    #'list_price': 0.0,
                    #'procure_method': 'make_to_order',
                    ##'description': description,
                    ##'description_spurchase'
                    ##'lst_price'
                    ##'seller_qty'
                    }
                if uom_id: 
                    data.update({
                        #'uos_id': uom_id,
                        'uom_id': uom_id,
                        'uom_po_id': uom_id,
                        })
                        
                if product_ids: # only update
                    try:
                        self.write(cr, uid, product_ids, data, context={
                            'lang': 'it_IT'})
                    except: # update via SQL in case of error
                        _logger.warning("Forced product %s uom %s" % (
                            product_ids[0],
                            uom_id,
                            ))
                        if uom_id: # update via SQL 
                            cr.execute(""" 
                                UPDATE product_template
                                SET uom_id = %s, uom_po_id = %s 
                                WHERE id in (
                                    SELECT product_tmpl_id 
                                    FROM product_product
                                    WHERE id = %s);
                            """, (uom_id, uom_id, product_ids[0]))
                            
                    
                    # Update language
                    for lang in language: # extra language
                        name = language.get(lang, False)
                        if name:
                            self.write(cr, uid, product_ids, {
                                'name': name,
                                'description_sale': name,
                                #'name_template': name,                                
                                }, context={
                                    'lang': lang})

                else:
                    _logger.error("Product not present: %s" % default_code)

            except:
                _logger.error("Product integration %s" % (sys.exc_info(), ))
                continue

        _logger.info("End product integration!")
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
