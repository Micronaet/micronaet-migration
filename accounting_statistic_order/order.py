# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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


class StatisticHeader(orm.Model):
    _name = 'statistic.header'

class StatisticOrder(orm.Model):
    '''Object that contain all order header coming from accounting
       This is only for statistic view or graph
    '''
    _name = 'statistic.order'
    _description = 'Statistic order'

    _order='sequence'

    _columns = {
        'name': fields.char('Description', size=64),
        'visible': fields.boolean('Visible',),
        'sequence': fields.integer('Sequence'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'property_account_position': fields.related('partner_id',
            'property_account_position', type='many2one',
            relation='account.fiscal.position', store=True,
            string='Fiscal position'),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)),
        'country_id': fields.related(
            'partner_id', 'country_id', type='many2one',
            relation='res.country', string='Country', store=True),
        'zone_id': fields.related(
            'partner_id', 'zone_id', type='many2one',
            relation='res.partner.zone', string='Zona', store=True),
        # Parte delle righe dettaglio:
        'code': fields.char('Code', size=24),
        'article': fields.char('Article', size=64),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'colli': fields.integer('Colli'),
        'quantity_ok': fields.float('Prodotti', digits=(16, 2)),
        'type': fields.selection([
            ('b','Prodotto'),
            ('n','Annullato'),
            ], 'Type of line'),
        'line_type': fields.selection([
            ('a','Articolo'),
            ('d','Descrizione'),
            ], 'Line type'),

        # Parte calcolata da visualizzare per prodotto:
        'total_linear_meter': fields.float('Total m/l', digits=(16, 2)),
        'total_volume': fields.float('Total volume', digits=(16, 2)),
        'total_weight': fields.float('Total weight', digits=(16, 2)),
        'note': fields.char('Note', size=64),

        'header_id': fields.many2one('statistic.header', 'Dettagli'),
        }

class StatisticHeader(orm.Model):
    _inherit = 'statistic.header'

    _order = 'deadline, name'
    _description = 'Testate ordini'

    # -------------------------------------------------------------------------
    #                           Scheduled procedure:
    # -------------------------------------------------------------------------
    def scheduled_import_order(self, cr, uid, file_input='~/etl/ocdetoerp.csv', 
            delimiter=';', header=0, verbose=100, context=None):
        ''' Import order for delivery report
        '''    
        # --------
        # Utility:
        # --------
        def get_partner_id(self, cr, uid, partner_id, context=None):
            ''' ID from partner
            '''
            partner_ids = self.pool.get('res.partner').search(cr, uid, [
                ('sql_customer_code', '=', partner_id)], context=context)
            if partner_ids:
                return partner_ids[0]
            return False
            
        _logger.info('Import CSV order file: %s' % file_input)
        #create_date = time.ctime(os.path.getctime(FileInput))    

        product_pool = self.pool.get('product.product')
        csv_pool = self.pool.get('csv.base')
        counter = -header
        lines = csv.reader(
            open(os.path.expanduser(file_input), 'rb'), delimiter=delimiter)

        # Remove all previous record:
        # > Header:
        header_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, header_ids, context=context) 
        # > Order:
        order_pool = self.pool.get('statistic.order')
        order_ids = order_pool.search(cr, uid, [], context=context) 
        order_pool.unlink(cr, uid, order_ids, context=context)

        # Load from CSV:
        tot_col = False
        header_id = 0
        old_order_number = ''
        sequence = 0
        import pdb; pdb.set_trace()
        for line in lines:
            try:
                counter += 1
                if counter <= 0: 
                    continue

                if not tot_col:
                    tot_col = len(line)
                    _logger.info('Total columns: %s' % tot_col)
                
                if tot_col != len(line):
                    _logger.error('Different columns (%s > %s)' % (
                        len(line), tot_col))
                    continue
                        
                # Read data:
                mexal_id = csv_pool.decode_string(line[0])
                cliente = csv_pool.decode_string(line[1]) 
                number = csv_pool.decode_string(line[2])
                order_date = csv_pool.decode_date(
                    line[3], with_slash=False) or False
                order_deadline = csv_pool.decode_date(
                    line[4], with_slash=False) or False
                articolo_id = csv_pool.decode_string(line[5]) 
                articolo = csv_pool.decode_string(line[6]) 
                quantity = csv_pool.decode_float(line[7])
                type_of_line = csv_pool.decode_string(line[8]) 
                note = csv_pool.decode_string(line[9]) 
                product_description = csv_pool.decode_string(line[10]) 
                product_description_eng = csv_pool.decode_string(line[11]) 
                colli = csv_pool.decode_string(line[12]) 
                line_type = csv_pool.decode_string(
                    line[13]).lower() # a=art, d=desc
                port_code = csv_pool.decode_string(line[14]).lower()
                port_description = csv_pool.decode_string(line[15]) 
                destination_description = csv_pool.decode_string(line[16]) 
                destination_address = csv_pool.decode_string(line[17]) 
                destination_cap = csv_pool.decode_string(line[18]) 
                destination_loc = csv_pool.decode_string(line[19]) 
                destination_prov = csv_pool.decode_string(line[20]) 
                registration_date = csv_pool.decode_date(
                    line[21], with_slash=False) or False
                extra_note = csv_pool.decode_string(line[22]) 
                agent_description = csv_pool.decode_string(line[23]) 

                # Dimensional fields:
                product_ids = product_pool.search(cr, uid, [
                    ('mexal_id','=', articolo_id)], context=context)

                if product_ids and line_type == 'a':
                    product_proxy = product_pool.browse(cr, uid, product_ids, 
                        context=context)[0]
                    total_linear_meter = (
                        quantity or 0.0) * product_proxy.linear_length
                    total_volume = (quantity or 0.0) * (
                        product_proxy.volume or 0.0)
                    total_weight = (quantity or 0.0) * (
                        product_proxy.weight or 0.0)
                else: # description line
                    total_linear_meter = False 
                    total_volume = False
                    total_weight = False 

                    if line_type == "a": 
                        _logger.error('Product not found: %s' % articolo_id)
                
                total = 0 #TODO
                partner_id = get_partner_id(
                    self, cr, uid, mexal_id, context=context)

                if not partner_id:
                    _logger.error('Partner not found %s' % mexal_id)
                    continue
                    
                if line_type=="a":
                    if not colli:
                        colli = quantity # if no cols use quantity (for 20 x 1)
                if port_code not in ('', 'f', 'a', 'd'):
                    _logger.error('%s) Destination not found: %s' % (
                        counter, port_code))
                if line_type not in ('a', 'd'):
                    _logger.error('%s) Line type not found: %s' % (
                        counter, line_type))
                if not partner_id:
                    _logger.error('%s) Partner not found: %s' % (
                        counter, mexal_id))
                if type_of_line.lower() == 'b':
                    quantity_ok = quantity or 0.0
                else:
                    quantity_ok = 0.0
                if not number:
                    _logger.error('%s) Order number not found: %s' % (
                        counter, number))
                   
                # Insert statistic.header
                # on change test or create else prev. ID
                if old_order_number != number: 
                    old_order_number = number # save old
                    counter += 1
                    sequence = 1
                    header = {
                        'name': number, #"Ordine n.:%s"%(number,),
                        'partner_id': partner_id,
                        'date': order_date,
                        'deadline': order_deadline,
                        #'total': fields.float('Total', digits=(16, 2)),
                        'note': note,
                        'port_code': port_code,
                        'port_description': port_description,
                        'destination': destination_description,
                        'destination_address': destination_address,
                        'destination_cap': destination_cap,
                        'destination_country': destination_loc,
                        'destination_prov': destination_prov,
                        'agent_description': agent_description,
                        # extra window:                          
                        'registration_date': registration_date,
                        'extra_note': extra_note,                                 
                        }

                    # TODO ottimizzabile cercando la rottura di codice:       
                    search_header_id = self.search(cr, uid, [
                        ('name','=',number)], context=context)
                    if search_header_id:
                        header_id = search_header_id[0] # Save for use in order
                    else: # Create:
                        header_id = self.create(
                            cr, uid, header, context=context)                            
                else: # same order
                    sequence += 1

                # Insert order detail (save with header_id)
                data = {
                    'name': number,
                    'partner_id': partner_id,
                    'date': order_date,
                    'deadline': order_deadline,
                    'total': total,
                    'code': articolo_id, # account code
                    'article': "%s %s" % (articolo, product_description),
                    'quantity': quantity,
                    'quantity_ok': quantity_ok,
                    'total_linear_meter': total_linear_meter,
                    'total_volume': total_volume,
                    'total_weight': total_weight,
                    'note': note,
                    'header_id': header_id, 
                    'line_type': line_type,
                    'colli': colli,
                    'sequence': sequence,
                    }
               
                # Error if not desc line
                if not order_deadline and line_type == "a": 
                    _logger.error('%s) Deadline not found: %s' % (
                        counter, number))
                
                elif order_deadline:
                    # TODO optimize! <<<<<<<<<<<
                    self.write(cr, uid, header_id, {
                        'deadline': order_deadline}, context=context) 

                if type_of_line:
                    data['type'] = type_of_line.lower()
                order_id = order_pool.create(cr, uid, data, context=context)                
            except:
                _logger.error('%s) Import order [%s]!' % (
                    counter, sys.exc_info()))

        _logger.info('End import order csv file: %s' % counter)
        return True

    def to_print(self, cr, uid, ids, context=None):
        header_mod=self.write(cr, uid, ids, {'print': True}, context=context)
        return True

    def no_print(self, cr, uid, ids, context = None):
        header_mod=self.write(cr, uid, ids, {'print': False}, context=context)
        return True

    def _function_order_header_statistic(
            self, cr, uid, ids, field_name, arg, context=None):
        """ Calcola i campi statistici nell'ordine
        """
        if context is None:
           context = {}

        res = {}
        for header in self.browse(cr, uid, ids, context=context):
            res[header.id] = {}
            res[header.id]['complete'] = True # initial value
            res[header.id]['total_item'] = 0.0
            res[header.id]['total_item_complete'] = 0.0
            res[header.id]['total_linear_meter'] = 0.0
            res[header.id]['total_linear_meter_ready'] = 0.0
            res[header.id]['total_volume'] = 0.0
            res[header.id]['total_volume_ready'] = 0.0
            res[header.id]['total_weight'] = 0.0
            for line in header.line_ids:
                res[header.id]['total_item'] += line.quantity or 0.0
                res[header.id][
                    'total_item_complete'] += line.quantity_ok or 0.0
                res[header.id][
                    'total_linear_meter'] += line.total_linear_meter or 0.0
                res[header.id][
                    'total_volume'] += line.total_volume or 0.0
                res[header.id][
                    'total_weight'] += line.total_weight or 0.0

                # test only A(rticle) line
                if line.line_type=='a' and not line.type=='b':
                    res[header.id]['complete'] = False

                if line.type=='b':
                   res[header.id][
                       'total_linear_meter_ready'] += line.total_linear_meter \
                           or 0.0
                   res[header.id][
                       'total_volume_ready'] += line.total_volume or 0.0
        return res


    _columns = {
        'name': fields.char('Numero ordine', size=16),
        'visible': fields.boolean('Visible',),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)), # TODO calcolato
        'note': fields.char('Note', size=64),
        'print': fields.boolean('To print'),

        'registration_date': fields.date('Registration date'),
        'extra_note': fields.char('Extra Note', size=64),

        'agent_description': fields.char('Agent description', size=36),

        'property_account_position': fields.related(
            'partner_id', 'property_account_position', type='many2one',
            relation='account.fiscal.position', store=True,
            string='Fiscal position'),
        'country_id': fields.related(
            'partner_id', 'country_id', type='many2one', relation='res.country',
            string='Country', store=True),
        'zone_id': fields.related(
            'partner_id', 'zone_id', type='many2one',
            relation='res.partner.zone', string='Zona', store=True),

        'line_ids': fields.one2many(
            'statistic.order', 'header_id', 'Linee dettaglio'),

        # Campi funzione:
        'complete': fields.function(
            _function_order_header_statistic, method=True, type='boolean',
            string='Completo', multi="statistiche", store=False),
        'total_item': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='N. art.', multi="statistiche",
            store=False),
        'total_item_complete': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='N. Art. (pronti)', multi="statistiche",
            store=False),
        'total_linear_meter': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Mt. lineari', multi="statistiche",
            store=False),
        'total_linear_meter_ready': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Mt. lineari (pronti)', multi="statistiche",
            store=False),
        'total_volume': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Volume', multi="statistiche", store=False),
        'total_volume_ready': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Volume (pronto)', multi="statistiche",
            store=False),
        'total_weight': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Peso', multi="statistiche", store=False),

        'port_code': fields.selection([
            ('f','Franco'),
            ('a','Assegnato'),
            ('d','Addebito'),
            ], 'Port'),
        'port_description': fields.char('Port description', size=40),
        'destination': fields.char('Destination ', size=40),
        'destination_address': fields.char('Destination address ', size=40),
        'destination_cap': fields.char('Destination cap', size=40),
        'destination_country': fields.char('destination country', size=40),
        'destination_prov': fields.char('destination province', size=40),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
