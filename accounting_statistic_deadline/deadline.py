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


class statistic_deadline(orm.Model):
    ''' Statistic tabled loaded only for manage deadline elements imported from
        accounting program
    '''
    _name = 'statistic.deadline'
    _description = 'Statistic deadline'
    _order = 'name,deadline' # name is loaded with partner name during import

    def schedule_csv_statistic_deadline_import(self, cr, uid, csv_file, 
            verbose=100, delimiter=';', header=0, context=None):
        ''' Scheduled importation for deadline 
        '''
        # Functions:
        def get_partner_info(self, cr, uid, partner_id, context=None):
            ''' Read partner and return credit limit
            '''
            if partner_id:
               partner_pool = self.pool.get('res.partner')
               partner_proxy = partner_pool.browse(
                   cr, uid, partner_id, context=context)
               if partner_proxy.fido_ko: # No credit limit
                  return -(
                      partner_proxy.saldo_c or 0.0) -(
                      partner_proxy.ddt_e_oc_c or 0.0)
               else:
                  return (
                      partner_proxy.fido_total or 0.0) - (
                      partner_proxy.saldo_c or 0.0) - (
                      partner_proxy.ddt_e_oc_c or 0.0)
            else:
               return 0.0

        _logger.info('Start import deadline on file: %s' % csv_file)
        
        # TODO Date file for log:
        #create_date = time.ctime(os.path.getctime(csv_file))    

        lines = csv.reader(
            open(os.path.expanduser(
                csv_file), 'rb'), delimiter=delimiter)
        counter = -header

        # Delete all:
        deadline_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, deadline_ids, context=context)
        
        # Pool used:
        partner_pool = self.pool.get('res.partner')
        invoice_pool = self.pool.get('account.invoice')
        csv_pool = self.pool.get('csv.base')
        
        # Load from CSV file:
        tot_col = 0
        account_balance = {}
        _logger.info('Start import payment')
        jumped_line = []
        jumped = 0
        for line in lines:
            try:
                if tot_col == 0: # the first time (for tot col)
                   tot_col = len(line)
                   _logger.info('Total column %s' % tot_col)
                   
                if counter < 0:  # jump header line
                    counter += 1
                else:   
                    counter += 1 
                    if not(len(line) and (tot_col == len(line))):
                        _logger.warning(
                            'Riga: %s Empty line of col different [%s!=%s]' % (
                                counter, 
                                tot_col, 
                                len(line),
                                ))
                        jumped += 1        
                        continue                   
                    try:
                        if counter % 50 == 0:
                            _logger.info('%s imported payment' % counter)

                        # Read parameters:    
                        mexal_id = csv_pool.decode_string(line[0])
                        deadline = csv_pool.decode_date(
                            line[1], with_slash=False) # YYYYMMDD
                        total = csv_pool.decode_float(line[2])
                        type_id = csv_pool.decode_string(line[3]).lower()
                        
                        # Extra data for invoice:
                        invoice_number = csv_pool.decode_string(line[4])
                        invoice_date = csv_pool.decode_date(
                            line[5], with_slash=False)                            
                        # TODO invoice_series = csv_pool.decode_string(line[5])                        
                        invoice_series = '1'
                        
                        # Calculated fields:
                        invoice_ref = 'FT/%s/%s/%06d' % (
                            invoice_series,
                            invoice_date[:4],
                            int(invoice_number), # TODO int with 0
                            )
                            
                        # TODO search invoice_id
                        invoice_id = False                                
                                               
                        if mexal_id[:2] == '20': # Supplier TODO parametrize
                           c_o_s = 's'
                           commento = 'Supplier'
                           total = -total
                        else:   
                           c_o_s = 'c'
                           commento = 'Customer'
                           
                        # Calculated field:               
                        if total > 0:
                           total_in = total
                           total_out = 0.0
                        else:
                           total_in = 0.0
                           total_out = -total
 
                        if mexal_id in account_balance:
                           account_balance[mexal_id] += total
                        else:
                           account_balance[mexal_id] = total
                        
                        # Get partner information:  
                        partner_ids = partner_pool.search(cr, uid, [
                            ('is_company', '=', True),
                            '|', ('sql_customer_code', '=', mexal_id),
                            ('sql_supplier_code', '=', mexal_id),
                            ], context=context)
                        if not partner_ids:    
                            _logger.error(
                                'Partner not found: %s' % mexal_id)
                            jumped += 1        
                            continue
                                
                        partner_proxy = partner_pool.browse(
                            cr, uid, partner_ids, context=context)[0]
                        
                        # only customer (TODO supplier)
                        scoperto_c = get_partner_info(
                            self, cr, uid, partner_ids[0], context=context) 
                        
                        # Import: statistic.order
                        name = '%s [%s]: %s (%s EUR)' % (
                            partner_proxy.name, mexal_id, deadline, total)
                        data = {
                            'name': name,
                            'partner_id': partner_proxy.id,
                            'deadline': deadline,
                            'total': total,
                            'in': total_in,
                            'out': total_out,
                            'type': type_id,
                            'c_o_s': c_o_s, 
                            
                            # Extra data:
                            'invoice_id': invoice_id,
                            'invoice_ref': invoice_ref,
                            'invoice_date': invoice_date,

                            #'deadline_real': deadline_real,
                            #'actualized': actualized,
                            }
                        if c_o_s == 'c':
                            data['scoperto_c'] = scoperto_c
                           
                        try:
                            deadline_id = self.create(
                                cr, uid, data, context=context)
                        except:
                            _logger.error('Row: %s - Deadline %s (%s) [%s]' % (
                                counter, deadline, name, sys.exc_info()))
                    except:
                        _logger.error('Row: %s - Import error [%s]' % (
                            counter, sys.exc_info()))
            except:
                _logger.error('Error import deadline')
                jumped += 1        
                continue
                
        _logger.info('Update partner information')
        for mexal_id in account_balance:
            if mexal_id.startswith('06'):
               cof = 'c'
            elif mexal_id.startswith('20'):
               cof = 's'   
            else:
                _logger.error('Not customer or supplier: %s' % mexal_id)
                continue

            item_ids = partner_pool.search(cr, uid, [
                ('is_company', '=', True),
                '|', ('sql_customer_code', '=', mexal_id),
                ('sql_supplier_code', '=', mexal_id),
                ], context=context) 
                
            if item_ids:
                partner_pool.write(cr, uid,item_ids, {
                    'saldo_' + cof: account_balance[mexal_id]
                    }, context=context)
            else:
               _logger.error('Not partner found: %s' % mexal_id)

        _logger.error('Jumped: %s partner' % jumped)
        _logger.info('Tot. deadline: %s' % counter)
        return True
         
    def _payment_is_deadlined(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        now = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        for payment in self.browse(cr, uid, ids, context=context):
            if payment.deadline < now:
                res[payment.id] = True
            else:
                res[payment.id] = False
        return res        

    _columns = {
        'name': fields.char('Deadline', size=64),
        'visible': fields.boolean('Visible'),

        'partner_id': fields.many2one('res.partner', 'Partner'),
        'type_cei': fields.related(
            'partner_id', 'type_cei', type='char', size=1,
            string='Fiscal position', store=True),
        'property_account_position': fields.related(
            'partner_id', 'property_account_position', type='many2one',
            relation='account.fiscal.position', store=True,
            string='Fiscal position'),
        'c_o_s': fields.char('Cust. or Supp.', size=1),
        'deadline': fields.date('Dead line'),
        'is_deadlined': fields.function(
            _payment_is_deadlined, method=True, 
            type='boolean', string='E\' scaduto', 
            store=True), 
                        
        'fido_date': fields.related(
            'partner_id', 'fido_date', type='date', 
            string='Credit limit date'),
        'fido_ko': fields.related(
            'partner_id', 'fido_ko', type='boolean', 
            string='Credit limit granted'),
        'fido_total': fields.related(
            'partner_id', 'fido_total',  type='float', digits=(16, 2),
            string='Credit limit amount'),

        'total': fields.float('Total', digits=(16, 2)),
        'in': fields.float('Income', digits=(16, 2)),
        'out': fields.float('Expense', digits=(16, 2)),

        # Non fatto related ma calcolato al volo
        'scoperto_c': fields.float('Found out customer', digits=(16, 2)),
        'scoperto_s': fields.float('Found out supplier', digits=(16, 2)),

        'saldo_c': fields.related(
            'partner_id', 'saldo_c', type='float', digits=(16, 2),
            string='Balance (customer)'),
        'saldo_s': fields.related(
            'partner_id', 'saldo_s', type='float', digits=(16, 2),
            string='Balance (customer)'),

        'ddt_e_oc_c': fields.related(
            'partner_id', 'ddt_e_oc_c', type='float', digits=(16, 2),
            string='DDT + OC opened (customer)'),
        'ddt_e_oc_s': fields.related(
            'partner_id', 'ddt_e_oc_s', type='float', digits=(16, 2),
            string='DDT + OC opened (supplier)'),

        'type': fields.selection([
            ('a', 'Addebito'),
            ('b', 'Bank transfer'),
            ('c', 'Cach'),
            ('r', 'RIBA'),
            ('t', 'Tratta'),
            ('m', 'Rimessa diretta'),
            ('x', 'Rimessa diretta X'),
            ('y', 'Rimessa diretta Y'),
            ('z', 'Rimessa diretta Z'),
            ('v', 'MAV'),
        ], 'Type', select=True),
        
        # Data used for FIDO computation
        'invoice_id': fields.many2one('account.invoice', 'Invoice'), 
        'invoice_ref': fields.char('Invoice ref.', size=64),     
        'invoice_date': fields.date('Invoice date'), # TODO change in related!    
        }
    
    _defaults = {
        'total': lambda *a: 0,
        'in': lambda *a: 0,
        'out': lambda *a: 0,
        'scoperto_c': lambda *a: 0,
        'scoperto_s': lambda *a: 0,
        }
    
class ResPartnerStatistic(orm.Model):
    """ res_partner_extra_fields
    """
    _inherit = 'res.partner'

    _columns = {
        'open_payment_ids': fields.one2many(
            'statistic.deadline', 'partner_id', 'Open payment'),
        }

class AccountInvoice(orm.Model):
    """ Add relation to invoice
    """
    _inherit = 'account.invoice'

    _columns = {
        'open_payment_ids': fields.one2many(
            'statistic.deadline', 'invoice_id', 'Open payment'),
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
