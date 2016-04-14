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
import shutil
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

transcode_month = { # to season element
    9: 1, # Sept
    10: 2,
    11: 3,
    12: 4,
    1: 5,
    2: 6, 
    3: 7,
    4: 8,
    5: 9,
    6: 10,
    7: 11, 
    8: 12,
    }

# fields selection:    
seasons = [
    (-100, 'Season old'), # all old seasons ex -1
    (-4, 'Season -4'),
    (-3, 'Season -3'),
    (-2, 'Season -2'), # ex 1
    (-1, 'Season -1'), # ex 2
    (1, 'Season current'), # ex 3
    (100, 'Season new'), # all new seasons ex 4
    ]

month_order_season = [
    (0, '00: Non trovato'),
    (1, '01: Set.'),
    (2, '02: Ott.'),
    (3, '03: Nov.'),
    (4, '04: Dic.'), 
    (5, '05*: Gen.'),
    (6, '06*: Feb.'),
    (7, '07*: Mar.'),
    (8, '08*: Apr.'),
    (9, '09*: Mag.'),
    (10, '10*: Giu.'),
    (11, '11*: Lug.'),
    (12, '12*: Ago.'),
    ]

def log_float(value):
    return ('%s' % value).replace('.', ',')
    
# -----------------------------------------------------------------------------
# Utility: TODO move somewhere!
# -----------------------------------------------------------------------------
def get_partner_name(self, cr, uid, partner_id, context=None):
    """ Partner ID from accounting code
    """
    if not partner_id:
        return False
    partner_proxy = self.pool.get('res.partner').browse(
        cr, uid, partner_id, context=context)
    return partner_proxy.name or False

# -----------------------------------------------------------------------------
#                              Objects:
# -----------------------------------------------------------------------------
class StatisticInvoiceAgent(orm.Model):
    """ Agent for customer, used in statistic grouping
    """
    _name = 'statistic.invoice.agent'
    _description = 'Invoice Agent'
    _order = 'name'

    _columns = {
        'name': fields.char('Agent', size=64, required=True),
        'ref': fields.char('Code', size=10),
        'hide_statistic': fields.boolean('Hide statistic'),
        }

class ResPartnerStatistic(orm.Model):
    """ res_partner_extra_fields
    """
    _inherit = 'res.partner'

    _columns = {
        'invoice_agent_id': fields.many2one(
            'statistic.invoice.agent', 'Invoice Agent'),
        }

# -----------------------------------------------------------------------------
#                            INVOICE:
# -----------------------------------------------------------------------------
class StatisticInvoice(orm.Model):
    """ Invoice analysis from accounting program
    """
    _name = 'statistic.invoice'
    _description = 'Statistic invoice'
    _order = 'month, name'

    # ----------------------------------
    # Utility:
    # ----------------------------------
    def append_csv_statistic_delivery_data(self, cr, uid, file_partner, 
            file_product, parent_max=False, delimiter=';', verbose=20,
            context=None):
        ''' Append OC non delivered from ODOO as statistics
            Append also document delivered from ODOO (from 01/01/2016)
        '''
        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def csv_format_float(value):
            ''' format 2 dec. comma separator
            '''
            if not value:
                return '0,00'
            
            try:
                return ('%15.2f' % float(value)).replace('.', ',')    
            except:  
                _logger.error('Error convert float: %s' % value)
                return '0,00'

        # ---------------------------------------------------------------------
        #                         Common Part:
        # ---------------------------------------------------------------------
        log_file1 = os.path.expanduser(
            '~/etl/stats.prod.%s.csv' % file_partner[-3:])
        log_f1 = open(log_file1, 'w')
        log_f1.write('Code|Month|Year|Remain #|Document|Remain Amount|Order\n')
        log_mask1 = '%s|%s|%s|%s|%s|%s|%s\n'

        log_file2 = os.path.expanduser(
            '~/etl/stats.partner.%s.csv' % file_partner[-3:])
        log_f2 = open(log_file2, 'w')
        log_f2.write('Code|Month|Year|Amount|Document|Num.\n')
        log_mask2 = '%s|%s|%s|%s|%s|%s\n'        
        
        today = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)

        # Copy file for write problem:
        file_partner_local = os.path.expanduser(
            '~/etl/partner.%s' % file_partner[-3:])
        file_product_local = os.path.expanduser(
             '~/etl/product.%s' % file_product[-3:])
        shutil.copyfile(file_partner, file_partner_local)     
        shutil.copyfile(file_product, file_product_local)     

        # Open for append:
        f_partner = open(file_partner_local, 'a')
        mask_partner = '%s;%2s;%10s;%15s;%s\n'
        f_product = open(file_product_local, 'a')
        mask_product = '%s;%2s;%10s;%10s;%s;%15s\n'
        
        # ---------------------------------------------------------------------
        #                           Orders:
        # ---------------------------------------------------------------------
        order_pool = self.pool.get('sale.order')
        order_ids = order_pool.search(cr, uid, [
            ('state', 'not in', ('cancel', 'draft', 'sent')),
            ('pricelist_order', '=', False), 
            ('mx_closed', '=', False),
            #('forecaster_production_id', '=', False), 
            ], context=context)
           
        type_document = 'OO'
        i = 0
        for order in order_pool.browse(cr, uid, order_ids, context=context):
            i += 1
            if i % verbose == 0:
                _logger.info('OC from ODOO read: %s' % i)
            #total = 0.0
            sql_customer_code = order.partner_id.sql_customer_code
            if not sql_customer_code:
                _logger.error('Partner code not found: %s' % (
                    order.partner_id.name, ))
                continue
            
            order_date_deadline = order.date_deadline or today
            for line in order.order_line:
                # Deadline in line data:
                date = line.date_deadline or order_date_deadline
                month = int(date[5:7])
                year = int(date[:4])    
                 
                if parent_max: # TODO check exist!!!
                    code = line.product_id.default_code[:parent_max]
                else:    
                    code = line.product_id.default_code
                     
                remain = line.product_uom_qty - line.delivered_qty
                if remain <= 0 or not line.product_uom_qty: # all delivered
                    continue
                remain_total = \
                    line.price_subtotal * remain / line.product_uom_qty
                total = remain_total # += # TODO remove keep remain_total
                 
                data = [ # product
                     code, 
                     month,
                     year,
                     int(remain),
                     type_document,
                     csv_format_float(remain_total),
                     ]
                     
                try:     
                    f_product.write(mask_product % tuple(data))
                    data.append(order.name)
                    log_f1.write(log_mask1 % tuple(data)) # product log
                except:    
                    #_logger.error('Error: %s' % (sys.exc_info()))
                    log_f1.write('||||||Error writing: %s!!!\n' % order.name)
                      
                if not total:
                    continue
            
                    
                data = [ # partner
                    sql_customer_code, # TODO check exist!!!
                    month,
                    year,
                    csv_format_float(total),
                    type_document,
                    ]

                try:    
                    # Append data on schedule import file:
                    f_partner.write(mask_partner % tuple(data))
                    
                    data[3] = log_float(data[3])
                    data.append(order.name)
                    log_f2.write(log_mask2 % tuple(data))
                except:    
                    #_logger.error('Error: %s' % (sys.exc_info()))
                    log_f1.write('%s|||||Error writing!!!\n' % order.name)

        # ---------------------------------------------------------------------
        #                             Delivery:
        # ---------------------------------------------------------------------
        ddt_pool = self.pool.get('stock.ddt')
        ddt_ids = ddt_pool.search(cr, uid, [
            ('invoice_id', '=', False),
            ], context=context)
            
        type_document = 'BO'
        i = 0
        for ddt in ddt_pool.browse(cr, uid, ddt_ids, context=context):
            i += 1
            if i % verbose == 0:
                _logger.info('DDT from ODOO read: %s' % i)
            total = 0.0
            date = ddt.date or today
            month = int(date[5:7])
            year = int(date[:4])            
            sql_customer_code = ddt.partner_id.sql_customer_code
            
            for line in ddt.ddt_lines:
                 if parent_max: # TODO check exist!!!
                     code = line.product_id.default_code[:parent_max]
                 else:
                     code = line.product_id.default_code
                     
                 number = line.product_uom_qty
                 sol = line.sale_line_id
                 if not sol.product_uom_qty:
                     continue
                     
                 # Proportional to ddt subtotal:    
                 amount = sol.price_subtotal * number / line.product_uom_qty
                 total += amount
                 
                 data = [
                      code, 
                      month,
                      year,
                      int(amount),
                      type_document,
                      csv_format_float(remain_total),                      
                      ]         
                 try:                  
                     f_product.write(mask_product % tuple(data))
                     data[3] = log_float(data[3])
                     data[5] = log_float(data[5])
                     data.append(ddt.name)
                     log_f1.write(log_mask1 % tuple(data))     
                 except:   
                     #_logger.error('Error: %s' % (sys.exc_info(), ))
                     log_f1.write('||||||Error writing: %s!!!\n' % ddt.name)

            if not total:
                continue
                
            if not sql_customer_code:
                _logger.error('Partner code not found: %s' % (
                    ddt.partner_id.name, ))
                continue
                
            data = [
                sql_customer_code, # TODO check exist!!!
                month,
                year,
                csv_format_float(total),
                type_document,
                ]
            try:
                f_partner.write(mask_partner % tuple(data))       
                data.append(ddt.name)
                data[3] = log_float(data[3])
                log_f2.write(log_mask2 % tuple(data))
            except:    
                 #_logger.error('Error: %s' % (sys.exc_info(), ))
                 log_f1.write('|||||Error writing: %s!!!\n' % ddt.name)
        
        # Close files:         
        f_partner.close()
        f_product.close()        
        return True

    # ----------------------------------
    # Importation procedure (scheduled):
    # ----------------------------------
    def schedule_csv_statistic_invoice_import(self, cr, uid,
            file_input1='~/ETL/fatmeseoerp1.csv',
            delimiter=';', header=0, verbose=100, context=None):
        """ Import statistic data from CSV file for invoice, trend, trendoc
            This particular importation are from 2 files (amount)
            (all particularity manage are use if particular = True)
        """        

        # ---------------------------------------------------------------------
        #                             Log part:
        # ---------------------------------------------------------------------
        _logger.info('Start invoice statistic for customer')
        log_file = os.path.expanduser(
            '~/etl/statistic.partner.%s.csv' % file_input1[-3:])
        log_f = open(log_file, 'w')
        log_f.write('#|Name|Code|Tag|# Month|Year|Season|Doc|Total|Zone|Agent|Zone type|Cat stat|Note\n')
        log_mask = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s\n'

        # File CSV date for future log
        #create_date=time.ctime(os.path.getctime(FileInput))

        # statistic.invoice:
        sql_pool = self.pool.get('micronaet.accounting')
        csv_base = self.pool.get('csv.base')
        partner_pool = self.pool.get('res.partner')

        # Clean database:
        invoice_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, invoice_ids, context=context)
        
        order_ref = datetime.now().strftime('%Y%m') # actualize order
        
        # ---------------------------------------------------------------------
        # Load dict for swap partner extra data
        # ---------------------------------------------------------------------
        # Agend and zone:
        _logger.info('Read partner extra info (zone, agent)')
        partner_extra = {}
        partner_ids = partner_pool.search(cr, uid, [], context=context)
        for partner in partner_pool.browse(cr, uid, partner_ids, 
                context=context):
            partner_extra[partner.id] = (
                partner.zone_id.name or '',
                partner.agent_id.name or '',
                '', #partner.zone_id.type.name or '',
                '', # TODO cat stat!!!                
                )

        # Destination in parent ID
        #_logger.info('Read parent for destinations conversion')
        #convert_destination = {}
        #cursor = sql_pool.get_parent_partner(cr, uid, context=context)
        #if not cursor:
        #    _logger.error("Unable to connect to parent (destination)!")
        #    return False # Fatal error!
        #else:
        #    for record in cursor:
        #        convert_destination[record['CKY_CNT']] = record[
        #            'CKY_CNT_CLI_FATT']
        #_logger.info(
        #    'Find %s destinations for conversion' % len(convert_destination))

        # Partner tags
        stats = {} # Statistic for partner
        partner_tags = {}
        tag_pool = self.pool.get('res.partner.category')
        tag_ids = tag_pool.search(cr, uid, [
            ('statistic', '=', True)], context=context)        
        for tag in tag_pool.browse(cr, uid, tag_ids, context=context):
            for partner in tag.partner_ids:
                partner_tags[partner.id] = tag.id # TODO problem in multi pres.

        csv_file = csv.reader(
            open(os.path.expanduser(file_input1), 'rb'),
            delimiter=delimiter,
            )

        # Current reference:
        current_year = datetime.now().year
        current_month = datetime.now().month
        counter = -header
        tot_col = 0
        # ---------------------------------------------------------------------
        #                    Read invoice data:
        # ---------------------------------------------------------------------
        for line in csv_file:
            note = '' # logging
            
            if tot_col == 0: # set cols (first time)
                tot_col = len(line)
                _logger.info('Total columns: %s' % tot_col)
            if counter < 0:
                counter += 1 # jump header line
                continue
                
            if not(len(line) and (tot_col == len(line))):
                _logger.error(
                   '%s) Empty or colums different [%s >> %s]' % (
                       counter, tot_col, len(line)))
                # Log:       
                log_f.write('%s|||||||||||||column different!\n' % counter)
                continue

            counter += 1
            try:
                mexal_id = csv_base.decode_string(line[0]) # ID
                month = int(csv_base.decode_string(line[1])) or 0 # jump is ''!
                month_season = transcode_month[month]
                year = csv_base.decode_string(line[2]) or ''
                total_invoice = csv_base.decode_float(
                    line[3]) or 0.0
                type_document = csv_base.decode_string(
                    line[4]).lower() # oc/bc/ft >> new: oo bo
                    
                # Jump old mexal elements:    
                if type_document in ('oc', 'bc'):
                    log_f.write(
                        '%s|||||||||||||Jump old OC or BC\n' % counter)                        
                    continue

                # -----------------        
                # Calculated field:
                # -----------------        
                partner_id = csv_base.get_create_partner_lite(
                    cr, uid, mexal_id, context=context)
                if not partner_id:
                    _logger.error(
                        '%s) Partner not found: %s' % (counter, mexal_id))
                    partner_name = '#ERR Partner code %s' % (mexal_id or '')
                else:
                    partner_name = get_partner_name(self, cr, uid, partner_id)
                    
                # Statistic database:    
                if partner_id not in stats:
                    stats[partner_id] = [
                        False, # Last operation
                        0.0, # invoiced current
                        0.0, # invoiced -1                                
                        0.0, # order current
                        ]

                if not total_invoice:
                    _logger.warning('%s Amount not found [%s]' % (
                        counter, line))
                    log_f.write(
                        '%s|||||||||||||Amount not found!\n' % counter)    
                    continue # Considered and error, jumped

                # Not classified (TODO but imported, true?!?!)
                if not (month or year):
                    note += 'Data (m or y) not found! '
                    _logger.error('%s Month / Year not found! %s' % (
                        counter, line))

                # OC old = today
                if type_document == 'oo' and '%s%02d' % (
                        year, month) < order_ref:
                    note += 'Change data ref. %s%s > %s' % (
                        year, month, order_ref)

                    _logger.warning(
                        '%s) Old OC OO > today: %s%02d, cliente: %s, '
                        'totale %s' % (
                            counter, year, month, mexal_id,
                            total_invoice))
                    year = datetime.now().strftime('%Y')
                    month = datetime.now().month
                    month_season = transcode_month[month] # recalculate

                data = {
                    'name': '%s [%s]' % (partner_name, mexal_id),
                    'partner_id': partner_id,
                    'tag_id': partner_tags.get(partner_id, False),
                    'month': month_season, # month,
                    'type_document': type_document,
                    'year': year,
                    'total': total_invoice,
                    }

                # Year to insert invoiced
                year_month = '%s%02d' % (year, month)
                
                # Season
                if current_month >= 1 and current_month <= 8:
                    ref_year = current_year - 1
                elif current_month >= 9 and current_month <= 12:
                    ref_year = current_year
                else:
                    _logger.error('%s) Month error not [1:12]' % (
                        counter))

                # september - current year >> august - next year
                if year_month >= '%s09' % ref_year and \
                        year_month <= '%s08' % (
                            ref_year + 1, ): # current
                    data['season'] = 1                   
                    # Stat value (current year)         
                    stats[partner_id][1] += total_invoice
                    if type_document == 'oo':
                        stats[partner_id][3] += total_invoice
                    
                elif year_month >= '%s09' % (
                        ref_year -1, ) and \
                        year_month <= '%s08' % (
                            ref_year, ): # year -1
                    data['season'] = -1
                    # Stat value (year-1)         
                    stats[partner_id][2] += total_invoice
                elif year_month >= '%s09' % (
                        ref_year -2, ) and \
                        year_month <= '%s08' % (
                            ref_year -1, ): # year -2
                    data['season'] = -2
                elif year_month >= '%s09' % (
                        ref_year -3, ) and \
                        year_month <= '%s08' % (
                            ref_year -2, ): # year -3
                    data['season'] = -3
                elif year_month >= '%s09' % (
                        ref_year -4, ) and \
                        year_month <= '%s08' % (
                            ref_year -3, ): # year -4
                    data['season'] = -4
                else: # extra interval (imported the same)
                    if year_month > '%s08' % (ref_year + 1):
                        data['season'] = 100 # new season
                    else:
                        data['season'] = -100 # old season

                # TODO find max date for stat last purchase:
                #stats[partner_id][0]                         

                # Common part (correct + amount)
                self.create(cr, uid, data, context=context)

                # Log:
                partner_extra_one = partner_extra.get(
                    partner_id, ['NO', 'NO', 'NO', 'NO'])
                log_f.write(log_mask % (
                    counter,
                    partner_name,
                    mexal_id,
                    data['tag_id'],
                    month_season,
                    year,
                    data['season'],
                    type_document,
                    log_float(total_invoice),
                    partner_extra_one[0], # zone
                    partner_extra_one[1], # agent
                    partner_extra_one[2], # type
                    partner_extra_one[3], # cat stat
                    note,
                    ))
            except:
                _logger.error('%s Error import invoice ID %s: [%s]' % (
                    counter, mexal_id, sys.exc_info()))

        # Set tot 20 partner:
        # TODO set only current year in test!
        _logger.info('Set top 15 partner invoiced in all years')
        cr.execute("""
            UPDATE statistic_invoice 
            SET top='t' 
            WHERE partner_id IN (
                SELECT partner_id 
                FROM statistic_invoice 
                GROUP BY partner_id 
                ORDER BY sum(total) desc 
                LIMIT 15);""")
                
        # For a bug: update zone_type:
        _logger.info('Update zone type for a bug')
        stat_ids = self.search(cr, uid, [
            ('zone_id', '!=', False)], context=context)
        for stat in self.browse(cr, uid, stat_ids, context=context):
            self.write(cr, uid, stat.id, {
                'zone_type': stat.zone_id.type, 
                }, context=context)    

        # Update partner stats:
        for partner_id in stats:
            #TODO invoice_trend = '='
            
            if stats[partner_id][2]:
                invoice_trend_perc = 100.0 * (
                    stats[partner_id][1] - stats[partner_id][2]) / \
                    stats[partner_id][2]
            else:
                invoice_trend_perc = 0.0

            partner_pool.write(cr, uid, partner_id, {
                 'last_activity': stats[partner_id][0],
                 'invoiced_current_year': stats[partner_id][1],
                 'invoiced_last_year': stats[partner_id][2],
                 'order_current_year': stats[partner_id][3],
                 
                 #'invoice_trend': invoice_trend,
                 'invoice_trend_perc': invoice_trend_perc,
                 }, context=context)
        _logger.info('Statistic invoice import terminated')
        return True

    _columns = {
        'name': fields.char('Descrizione', size=64),
        'visible': fields.boolean('Visible'), # TODO remove
        'top': fields.boolean('Top'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'tag_id': fields.many2one('res.partner.category', 'Tag'),
        'invoice_agent_id': fields.related('partner_id', 'invoice_agent_id',
            type='many2one', relation='statistic.invoice.agent',
            string='Invoice agent', store=True),
        'hide_statistic': fields.related('invoice_agent_id', 'hide_statistic',
            type='boolean', string='Nascondi statistica', store=True),
        'type_cei': fields.related('partner_id', 'type_cei', type='char',
            size=1, string='C E I', store=True),
        'total': fields.float('Stag. attuale', digits=(16, 2)),

        'type_document': fields.selection([
            ('ft', 'Fattura'),
            ('oc', 'Ordine Mexal'),
            ('oo', 'Ordine ODOO'),
            ('bc', 'DDT Mexal'), 
            ('bo', 'DDT ODOO'), 
            ], 'Tipo doc.', select=True),

        'month': fields.selection(month_order_season, 'Mese', select=True),
        'season': fields.selection(seasons, 'Season', select=True),
        'year': fields.char('Anno', size=4),

        # Extra info for filter graph:
        'statistic_category_id': fields.related('partner_id', 
            'statistic_category_id', type='many2one',
            relation='statistic.category', string='Statistic category', 
            store=True),

        'trend': fields.related('statistic_category_id', 'trend', 
            type='boolean', readonly=True, string='Trend stat. cat.', 
            store=True),

        # TODO moved in new module: mx_partner_zone:
        'zone_id': fields.related('partner_id', 'zone_id', type='many2one',
            relation='res.partner.zone', string='Zone', store=True),
        # Related won't work!
        #'zone_type': fields.related('zone_id', 'type', type='selection',
        #    selection=[
        #        ('region', 'Region'),
        #        ('state', 'State'),
        #        ('area', 'Area'), ], string='Type', store=True),
        'zone_type': fields.selection([
            ('region', 'Region'),
            ('state', 'State'),
            ('area', 'Area'), ], 'Zone type'),
        'country_id': fields.related('partner_id', 'country_id',
            type='many2one', relation='res.country', string='Country',
            store=True),
        }

    _defaults = {
        'total': lambda *a: 0.0,
        'visible': lambda *a: False,
        }

# -----------------------------------------------------------------------------
#                            PRODUCT
# -----------------------------------------------------------------------------
class StatisticInvoiceProduct(orm.Model):
    """ Statistic on product:
        Partner - month - product = key
    """
    _name = 'statistic.invoice.product'
    _description = 'Statistic invoice'
    _order = 'month, name'

    def schedule_csv_statistic_invoice_product_import(self, cr, uid,
            input_file, delimiter=';', header=0, verbose=100, load_line=False, 
            context=None):
        """ Schedule procedure for import statistic.invoice.product
            self: instance
            cr: cursor
            uid: user ID
            input_file: input file (use ~ as home position)
            delimiter: separator for csv file
            header: total line of header
            verbose: every X record print log (0 = no log)
            load_line: if present load family element and get line
            context:
            
        """
        # TODO for log check:
        #create_date=time.ctime(os.path.getctime(FileInput))
        input_file = os.path.expanduser(input_file)
        _logger.info('Start importation product invoice stats: %s' % (
            input_file))
        csv_lines = csv.reader(open(input_file, 'rb'), delimiter=delimiter)
        counter = -header

        item_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, item_ids, context=context)

        # Family categorization (create dict for association):
        template_pool = self.pool.get('product.template')
        family_ids = template_pool.search(cr, uid, [
            ('is_family', '=', True)], context=context)
        families = {}
        for family in template_pool.browse(
                cr, uid, family_ids, context=context):
            families.update(
                dict.fromkeys(
                    family.family_list.split('|'), (
                        family.id, family.categ_id.id)))
                        
        # Load line if necessary (family = code, not parent part!)
        lines = {}
        if load_line:
            product_pool = self.pool.get('product.product')
            product_ids = product_pool.search(cr, uid, [], context=context)            
            for product in product_pool.browse(
                    cr, uid, product_ids, context=context):                    
                try:    
                    if product.line_id.id:
                        lines[product.default_code] = product.line_id.id
                except:
                    continue # jump error    

        # Create list for family to remove:
        remove_pool = self.pool.get('statistic.invoice.product.removed')
        item_ids = remove_pool.search(cr, uid, [], context=context)
        family_blacklist = [
            item.name.upper() for item in remove_pool.browse(
                cr, uid, item_ids, context=context)]

        top_limit = 0.005 # TODO parametrize
        tot_col = 0
        season_total = 0
        item_invoice = {}
        order_ref = datetime.now().strftime('%Y%m') # actualize order
        current_year = datetime.now().year
        current_month = datetime.now().month
        csv_base = self.pool.get('csv.base')        
        for line in csv_lines:
            try:
                if counter < 0:
                    counter += 1
                    continue

                if not tot_col: # save total cols
                   tot_col = len(line)
                   _logger.info('Total cols %s' % tot_col)

                if not (len(line) and (tot_col == len(line))):
                    _logger.warning('%s) Empty line or column err [%s>%s]' % (
                        counter, tot_col, len(line)))
                    continue

                counter += 1
                # Read fields from csv file:
                name = csv_base.decode_string(line[0]).upper() # Family
                if name in family_blacklist:
                    continue # jump record
                month = csv_base.decode_string(line[1])
                year = csv_base.decode_string(line[2])
                total_invoice = csv_base.decode_float(line[3]) or 0.0
                type_document = csv_base.decode_string(line[4]).lower()

                if not year or not month:
                    _logger.warning('%s) Period not found!' % counter)
                    continue

                month = int(month)
                month_season = transcode_month[month]

                # Calculated field:
                if type_document not in ('ft', 'bo', 'oo'):
                    _logger.warning('%s) Type of doc not correct: %s' % (
                        counter, type_document))
                    type_document = False # not jumperd

                # Actualize OO
                if type_document == 'oo' and '%s%02d' % (
                        year, month) < order_ref:                                    
                    _logger.warning('%s) Old OO > today: %s%02d totale %s' % (
                        counter, year, month, total_invoice))
                    year = datetime.now().strftime('%Y')
                    month = datetime.now().month
                    month_season = transcode_month[month] # recalculate
                
                family_id, categ_id = families.get(name, (False, False))

                data = {
                    'name': name,
                    'month': month_season,
                    'type_document': type_document,
                    'total': total_invoice, # now for all seasons
                    'year': year,
                    'family_id': family_id,
                    'categ_id': categ_id,
                    'line_id': lines.get(name, False), # if not request is {}
                    }

                # Which year
                if not (year or month):
                    _logger.error(
                        '%s) Year %s or month %s not found (jump)' % (
                            counter, year, month))
                    continue

                season_total += total_invoice
                year_month = '%s%02d' % (year, month)

                if current_month >= 1 and current_month <= 8:
                    ref_year = current_year - 1
                elif current_month >= 9 and current_month <= 12:
                    ref_year = current_year
                else:
                    _logger.error('%s) Month error (jump)' % counter)
                    continue

                # TODO: add also OC
                if year_month >= '%s09' % ref_year and \
                        year_month <= '%s08' % (ref_year + 1):
                    data['season'] = 1
                elif year_month >= '%s09' % (ref_year -1) and \
                       year_month <= '%s08' % ref_year: # -1
                    data['season'] = -1
                elif year_month >= '%s09' % (ref_year -2) and \
                        year_month <= '%s08' % (ref_year -1): #-2
                    data['season'] = -2
                else:
                    _logger.warning('%s) Extra period %s-%s' % (
                        counter, year, month))
                    if year_month > '%s08' % (ref_year + 1):
                        data['season'] = 100 # extra (new period)
                    else:
                        data['season'] = -100 # extra (old period)

                # Sum total for element
                if name not in item_invoice:
                    item_invoice[name] = total_invoice
                else:
                    item_invoice[name] += total_invoice

                self.create(cr, uid, data, context=context)
            except:
                _logger.error('%s) Error import record [%s]' % (
                   counter, sys.exc_info()))

        _logger.info(
            'End importation records, set top elements')

        try: # Split product depend on invoiced
            most_popular = []
            for family in item_invoice:
                perc_invoice = item_invoice[family] / season_total
                if perc_invoice >= top_limit and family not in most_popular:
                    most_popular.append(family)

            top_ids = self.search(cr, uid, [
                ('name', 'in', most_popular)], context=context)
            self.write(cr, uid, top_ids, {'top': True}, context=context)
            _logger.info('End importation')

        except:
            _logger.error('%s) Error create record [%s]' % (
                counter, sys.exc_info()))
        return True

    _columns = {
        'name': fields.char('Product family', size=64),
        'visible': fields.boolean('Visible'), # TODO removeable!
        'top': fields.boolean('Top sale'),
        'total': fields.float('Amount', digits=(16, 2)),

        'family_id': fields.many2one('product.template', 'Family'),
        'categ_id': fields.many2one('product.category', 'Family'), 
        
        # Categorization fields:
        'line_id': fields.many2one('product.line', 'Line'), 
        #'line_id': fields.related(
        #    'family_id', 'line_id', 
        #    type='many2one', relation='product.line', 
        #    string='Line', store=True),             
        
        # Not used for now:    
        'tipology_id': fields.related(
            'family_id', 'tipology_id', 
            type='many2one', relation='product.tipology', 
            string='Tipology', store=True), 
        'material_id': fields.related(
            'family_id', 'material_id', 
            type='many2one', relation='product.material', 
            string='Material', store=True), 

        'percentage': fields.float(
            '% 3 season total', digits=(16, 5)),

        'season': fields.selection(seasons, 'Season', select=True),

        'year': fields.char('Anno', size=4),

        'type_document': fields.selection([
            ('ft', 'Fattura'),
            ('oc', 'Ordine'),
            ('bc', 'DDT'),
            ], 'Doc. type', select=True), # togliere?

        'month': fields.selection(month_order_season, 'Month', select=True),
        }

    _defaults = {
        'total': lambda *a: 0.0,
        'top': lambda *a: False,
        }

class ResPartnerCategory(orm.Model):
    """ Add fields for statistic purpose
    """
    _inherit = 'res.partner.category'

    _columns = {
        'statistic': fields.boolean('Statistic')
        # TODO m2m per partner tags
        }

class StatisticInvoiceProductRemoved(orm.Model):
    """ Product not present in statistic
    """
    _name = 'statistic.invoice.product.removed'
    _description = 'Statistic Product to remove'

    _columns = {
        'name': fields.char('Family', size=64, required=True),
        }

class ResPartnerStatistic(orm.Model):
    """ res_partner_extra_fields
    """
    _inherit = 'res.partner'

    _columns = {
        'trend': fields.boolean(
            'Trend',
            help='Insert in trend statistic, used for get only interesting '
                'partner in statistic graph'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
