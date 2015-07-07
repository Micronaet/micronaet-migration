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
import xmlrpclib
import csv
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

class StatisticStore(orm.Model):
    ''' Object that store data from 2 company for mix store values
        using protocol to link product from Company 1 to Company 2
    '''

    _name = 'statistic.store'
    _description = 'Store info'
    _rec_name = "product_code"
    _order = "product_code,product_description"

    def schedule_csv_import_store(
            file_input1='~/ETL/esistoerprogr.CM1',
            file_input2='~/ETL/esistoerprogr.CM2',  
            exch_file1='~/ETL/cm1-cm2.CM1',
            exch_file2='~/ETL/cm1-cm2.CM2',
            delimiter=';', header=0, verbose=100):
        ''' Scheduled importation of existence
        '''
        # TODO test prepare function in csv module    

        # Remove all previous data:
        stock_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, stock_ids, context=context)

        records = {'FIA': {}, 'GPB': {}} # TODO

        # Load pack for product:
        q_x_packs = {'FIA': {}, 'GPB': {}}

        product_pool = self.pool.get('product.product')
        pack_ids = product_pool.search(cr, uid, [], context=context)
        
        # first company:
        for item in product_pool.browse(cr, uid, pack_ids, context=context):
            q_x_packs["FIA"][item.default_code] = item.q_x_pack
        
        # second company:
        # TODO XML-RPC
        pack_ids = sock_gpb.execute(dbname, uid_gpb, pwd, 'product.product', 'search', [])
        for item in sock_gpb.execute(dbname, uid_gpb, pwd, 'product.product', 'read', pack_ids, ('q_x_pack','default_code')):
            q_x_packs["GPB"][item['default_code']] = item['q_x_pack']

        loops = [
            ("FIA", file_input1, exch_file1), 
            ("GPB", file_input2, exch_file2),
            ]
        for azienda, f, f_exch in loops:    
            file_csv = os.path.expanduser(f)

            lines = csv.reader(open(file_csv, 'rb'), delimiter=delimiter)
            counter = -header

            for line in lines:
                try:
                    counter += 1 
                    if counter <= 0:  # jump n lines of header 
                        continue

                    ref = Prepare(line[0]) 
                    product_description = Prepare(line[1]).title() 
                    product_um = Prepare(line[2]).upper()
                    inventary = PrepareFloat(line[3]) or 0.0
                    value_in = PrepareFloat(line[4]) or 0.0 
                    value_out = PrepareFloat(line[5]) or 0.0 
                    balance = PrepareFloat(line[6]) or 0.0 
                    supplier_order = PrepareFloat(line[7]) or 0.0 
                    customer_order = PrepareFloat(line[8]) or 0.0 
                    customer_order_auto = PrepareFloat(line[9]) or 0.0 
                    customer_order_suspended = PrepareFloat(line[10]) or 0.0 
                    supplier = Prepare(line[11]).title()
                    product_description += "\n" + (Prepare(line[12]).title() or '') 
                    mexal_s = Prepare(line[13]) or False
                   
                    # Calculated fields:
                    company = azienda.lower()
                    availability = (
                        balance + supplier_order - 
                        customer_order - customer_order_suspended) 
                        # E + F - I - S TODO auto??
                    product_um2 = ''
                    inventary_last = 0.0
                    q_x_pack = q_x_packs[azienda][ref] if ref in q_x_packs[
                        azienda] else 0
                    
                    records[azienda][ref] = {
                        'company': company, 
                        'supplier': supplier,
                        'mexal_s': mexal_s, 
                        'product_code': ref,
                        'product_description': product_description,
                        'product_um': product_um,
                        'q_x_pack': q_x_pack,

                        # Value fields
                        'inventary': inventary,
                        'q_in': value_in,
                        'q_out': value_out,
                        'balance': balance,
                        'supplier_order': supplier_order,
                        'customer_order': customer_order,
                        'customer_order_auto': customer_order_auto,
                        'customer_order_suspended': 
                            customer_order_suspended,

                        # Field calculated:
                        'availability': availability,
                        'product_um2': product_um2,
                        'inventary_last': inventary_last,
                        }
                except:
                    _logger.error('Error import line: %s' % (
                        sys.exc_info(),))
                    continue    

            # Sell from CM1 to CM2 (subtract from q_in sum to q_out:
            file_exchange = os.path.expanduser(f_exch)
            lines = csv.reader(
                open(file_exchange, 'rb'), delimiter=delimiter)

            for line in lines:
                if len(line): # jump empty lines
                    ref = Prepare(line[0])
                    value_sale = PrepareFloat(line[1]) or 0.0
                    if ref in records[azienda]:
                        # also for unload number is positive
                        records[azienda][ref]['q_in'] -= value_sale
                        records[azienda][ref]['q_out'] -= value_sale 
               
        comment = ""
        for azienda in ["FIA", "GPB"]:
            if azienda == "FIA":
               altra_azienda="GPB"
            else:   
               altra_azienda="FIA"
               
            for item in records[azienda].keys():            
                if ((azienda == "FIA") and (item[:1] == "C") and (
                        item[1:] in records["GPB"])) or (
                        (azienda=="GPB") and (item[:1]=="F") and (
                        item[1:] in records["FIA"])): # jump other CM items

                    # Do nothing (sum in other company)
                    # Jump
                    print "Riga: [%s] SALTATO [%s] %s" % (
                        azienda, item, 
                        records[azienda][item]['product_description'])
                elif (
                        (azienda=="FIA") and (
                        "F" + item in records["GPB"])) or (
                        (azienda=="GPB") and (
                        "C" + item in records["FIA"])): # Sum item this CM
                    # double
                    if azienda == "FIA": 
                        item_other = "F" + item 
                    else:   
                        item_other = "C" + item 

                    data_store = {   
                        'company': records[azienda][item]['company'], 
                        'supplier': records[azienda][item]['supplier'], 
                        'product_code': records[azienda][item][
                            'product_code'],
                        'product_description': records[azienda][item][
                            'product_description'],
                        'product_um': records[azienda][item]['product_um'],

                        'inventary': records[azienda][item][
                            'inventary'] + records[altra_azienda][
                                item_other]['inventary'],   
                        'q_x_pack': records[azienda][item]['q_x_pack'],
                        'q_in': records[azienda][item]['q_in'] + records[
                            altra_azienda][item_other]['q_in'],
                        'q_out': records[azienda][item]['q_out'] + \
                            records[altra_azienda][item_other]['q_out'],
                        'balance': records[azienda][item]['balance'] + \
                            records[altra_azienda][item_other]['balance'],
                        'supplier_order': records[azienda][item][
                            'supplier_order'] + \
                            records[altra_azienda][item_other][
                                'supplier_order'],
                        'customer_order': records[azienda][item][
                            'customer_order'] + records[altra_azienda][
                                item_other]['customer_order'],
                        'customer_order_auto': records[azienda][item][
                            'customer_order_auto'] + records[
                                altra_azienda][item_other][
                                    'customer_order_auto'],
                        'customer_order_suspended': records[azienda][item][
                            'customer_order_suspended'] + records[
                                altra_azienda][item_other][
                                    'customer_order_suspended'],

                        'availability': records[azienda][item][
                            'availability'] + records[altra_azienda][
                                item_other]['availability'],
                        'product_um2':  records[azienda][item][
                            'product_um2'],
                        'inventary_last':  records[azienda][item][
                            'inventary_last'],

                        'both': True, # for elements present in both company
                        }
                    self.create(cr, uid, data_store, context=context)
                else: # Normal (no intersection)
                    self.create(cr, uid, records[azienda][item], 
                        context=context)
        
        return True

    _columns = {
        # Extra info calculated:
        'company':fields.selection([
                ('gpb','G.P.B.'),
                ('fia','Fiam'),
                ], 'Company', select=True),

        # Product info:
        'mexal_s': fields.char('Mexal ID', size=10),
        'supplier': fields.char('Supplier', size=68),
        'product_code': fields.char('Product code', size=24),
        'q_x_pack': fields.integer('Q. x pack'),
        'product_description': fields.char('Product description', size=128),
        'product_um': fields.char('UOM', size=4),

        # Value fields
        'inventary': fields.float('Inventary', digits=(16, 2)),
        'q_in': fields.float('In', digits=(16, 2)),
        'q_out': fields.float('Out', digits=(16, 2)),
        'balance': fields.float('Existent', digits=(16, 2)),
        'supplier_order': fields.float('OF', digits=(16, 2)),
        'customer_order': fields.float('OC imp.', digits=(16, 2)),
        'customer_order_auto': fields.float(
            'OC automatic in prod.', digits=(16, 2)),
        'customer_order_suspended': fields.float(
            'OC suspended', digits=(16, 2)),

        # Field calculated:
        'availability': fields.float('Dispo lord', digits=(16, 2)),
        'product_um2': fields.char('UM2', size=4),
        'inventary_last': fields.float('Manual inventary', digits=(16, 2)),

        'both': fields.boolean('Entrambe',
            help="Esiste in entrambe le aziende"),
        }

    _defaults = {
        'both': lambda *a: False,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
