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


# Utility: TODO move somewhere!
def get_partner_name(self, cr, uid, partner_id, context=None):
    ''' Partner ID from accounting code
    '''
    if not partner_id:
        return False
    partner_proxy = self.pool.get('res.partner').browse(
        cr, uid, partner_id, context=context)
    return partner_proxy.name or False

class StatisticInvoiceAgent(orm.Model):
    _name = 'statistic.invoice.agent'
    _description = 'Invoice Agent'

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
        
class StatisticTrend(orm.Model):
    _name = 'statistic.trend'
    _description = 'Statistic Trend'

    def _function_index_increment(self, cr, uid, ids, field_name=None,
            arg=False, context=None):
        """ Best increment on previous year
        """
        if context is None:
           context = {}

        result = {}
        for item in self.browse(cr, uid, ids, context=context):
            result[item.id]={}
            increment=(item.total or 0.0) - (item.total_last or 0.0)
            if increment > 0: #increment (best)
               result[item.id]['best']=increment or 0.0
               result[item.id]['worst']= 0.0
            else: # decrement (worst)
               result[item.id]['worst']=-increment or 0.0
               result[item.id]['best']= 0.0
        return result

    _columns = {
        'name': fields.char('Description', size=64),
        'visible': fields.boolean('Visible',),

        'partner_id': fields.many2one('res.partner', 'Partner'),

        'percentage': fields.float(
            '% sul fatt. attuale', digits=(16, 5)),
        'percentage_last': fields.float(
            '% sul fatt. stag. -1', digits=(16, 5)),
        'percentage_last_last': fields.float(
            '% sul fatt. stag. -2', digits=(16, 5)),
        'percentage_last_last_last': fields.float(
            '% sul fatt. stag. -5', digits=(16, 5)),
        'percentage_last_last_last_last': fields.float(
            '% sul fatt. stag. -4', digits=(16, 5)),

        'total': fields.float('Tot. stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Tot. stag. -1', digits=(16, 2)),
        'total_last_last': fields.float('Tot. stag. -2', digits=(16, 2)),
        'total_last_last_last': fields.float('Tot. stag. -3', digits=(16, 2)),
        'total_last_last_last_last': fields.float('Tot. stag. -4', 
            digits=(16, 2)),

        'trend_category': fields.related(
            'partner_id', 'trend_category', type='boolean', readonly=True,
            string='Categoria trend'),
        'statistic_category_id': fields.related(
            'partner_id', 'statistic_category_id', type='many2one',
            relation="statistic.category", readonly=True,
            string='Categoria statistica partner'),
        'trend': fields.related(
            'partner_id', 'trend', type='boolean', readonly=True,
            string='Important partner'),

        'type_document': fields.selection([
            ('ft','Fattura'),
            ('oc','Ordine'),
            ('bc','DDT'),
            ], 'Tipo doc.', select=True),

        'best': fields.function(
            _function_index_increment, method=True, type='float',
            string='Best trend', multi='indici', store=True,),
        'worst': fields.function(
            _function_index_increment, method=True, type='float',
            string='Worst trend', multi='indici', store=True,),
        }

class StatisticTrendOc(orm.Model):
    ''' Prototipe for statistic that has OC in total amount 
    '''
    _name = 'statistic.trendoc'
    _inherit = 'statistic.trend'
    _description = 'Statistic Trend OC'

class StatisticInvoice(orm.Model):
    ''' Invoice analysis from accounting program
    '''
    _name = 'statistic.invoice'
    _description = 'Statistic invoice'
    _order = 'month, name'

    # ----------------------------------
    # Importation procedure (scheduled):
    # ----------------------------------
    def schedule_csv_statistic_invoice_import(self, cr, uid, 
            file_input1='~/ETL/fatmeseoerp1.csv', 
            file_input2='~/ETL/fatmeseoerp2.csv', 
            delimiter=';', header=0,
            verbose=100, context=None): 
        ''' Import statistic data from CSV file for invoice, trend, trendoc
        '''

        # ---------------------------------------------------------------------
        #                          COMMON PART
        # ---------------------------------------------------------------------
        _logger.info('Start invoice statistic importation (trend and trendoc)')
        
        # File CSV date for future log
        #create_date=time.ctime(os.path.getctime(FileInput))

        csv_base = self.pool.get('csv.base')

        # Delete all record:
        trend_pool = self.pool.get('statistic.trend')
        trend_ids = trend_pool.search(cr, uid, [], context=context)
        trend_pool.unlink(cr, uid, trend_ids, context=context)
        
        trendoc_pool = self.pool.get('statistic.trendoc')
        trendoc_ids = trendoc_pool.search(cr, uid, [], context=context)
        trendoc_pool.unlink(cr, uid, trendoc_ids, context=context)

        # statistic.invoice:
        invoice_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, invoice_ids, context=context)
                
        # ---------------------------------------------------------------------
        #                  STATISTIC.INVOICE IMPORT
        # ---------------------------------------------------------------------
        # TODO portare parametrizzandolo in OpenERP:
        p1_id = csv_base.get_create_partner_lite(
            cr, uid, '06.02209', context=context)
        p2_id = csv_base.get_create_partner_lite(
            cr, uid, '06.01537', context=context)            
        customer_replace = {
            '06.40533': (
                ('06.02209', p1_id, get_partner_name(self, cr, uid, p1_id), ),
                ('06.01537', p2_id, get_partner_name(self, cr, uid, p2_id), ),
                )}

        loop_steps = {
            1: csv.reader(
                open(os.path.expanduser(file_input1), 'rb'), 
                delimiter=delimiter),
            2: csv.reader(
                open(os.path.expanduser(file_input2), 'rb'), 
                delimiter=delimiter),
            }

        try:
            for step, lines in loop_steps.iteritems():
                counter = -header
                tot_col = 0
                for line in lines:
                    if tot_col == 0: # set cols (first time)
                        tot_col = len(line)
                        _logger.info('Total columns: %s' % tot_col)
                    if counter < 0:
                        counter += 1 # jump header line
                    else:
                        if not(len(line) and (tot_col == len(line))):
                            _logger.warning(
                               '%s) Empty or colums different [%s >> %s]' % (
                                   counter, tot_col, len(line)))
                            continue
                            
                        counter += 1
                        try:
                            mexal_id = csv_base.decode_string(line[0]) # ID
                            month = int(csv_base.decode_string(line[1])) or 0
                            year = csv_base.decode_string(line[2]) or '' 
                            total_invoice = csv_base.decode_float(
                                line[3]) or 0.0
                            type_document = csv_base.decode_string(
                                line[4]).lower() # oc/ft

                            if step == 2: # 2nd loop is different:
                                if mexal_id not in customer_replace:
                                    continue # jump if not a replace partner

                                # Alias customer for add the profit:
                                old_mexal_id = mexal_id
                                mexal_id = customer_replace[
                                    old_mexal_id][0][0]
                                partner_id = customer_replace[
                                    old_mexal_id][0][1]
                                partner_name = customer_replace[
                                    old_mexal_id][0][2]

                                # Agent with subtract loss
                                mexal_id2 = customer_replace[
                                    old_mexal_id][1][0]
                                partner_id2 = customer_replace[
                                    old_mexal_id][1][1]
                                partner_name2 = customer_replace[
                                    old_mexal_id][1][2]

                            else: # 1st loop is different:
                                # Problem Customer: M Business:
                                if mexal_id in (
                                    '06.00052', '06.00632', '06.01123', 
                                    '06.01125', '06.01126', '06.01127', 
                                    '06.01129', '06.01131', '06.01132', 
                                    '06.01136', '06.01137', '06.01138', 
                                    '06.01139', '06.01142', '06.01143', 
                                    '06.01146', '06.01147', '06.01149', 
                                    '06.01151', '06.01153', '06.01154', 
                                    '06.01155', '06.01159', '06.01161',
                                    '06.01163', '06.01164', '06.01165', 
                                    '06.01166', '06.01167', '06.01168', 
                                    '06.01170', '06.01171', '06.01175', 
                                    '06.01177', '06.01178', '06.01179',
                                    '06.01221', '06.01231', '06.01260', 
                                    '06.01317', '06.01386', '06.01408', 
                                    '06.01416', '06.01420', '06.01421', 
                                    '06.01424', '06.01436', '06.01439',
                                    '06.01481', '06.01501', '06.01532', 
                                    '06.01538', '06.01580', '06.01609', 
                                    '06.01764', '06.01797', '06.02081', 
                                    '06.02117', '06.02348', '06.02408',
                                    '06.02409', '06.02709', '06.02888', 
                                    '06.03043', '06.03629', '06.03788', 
                                    ):
                                    
                                    _logger.warning(
                                        "%s: replace code: %s>06.03044" % (
                                            counter, mexal_id))
                                    mexal_id = '06.03044'

                                # Calculated field:
                                partner_id = csv_base.get_create_partner_lite(
                                    cr, uid, mexal_id, context=context)
                                if not partner_id:
                                    _logger.error(
                                        "%s) Partner not found: %s" % (
                                        counter, mexal_id))
                                    partner_name = "#ERR Partner code %s" % (
                                        mexal_id or "")
                                else:
                                    partner_name = get_partner_name(
                                        self, cr, uid, partner_id)

                            if not total_invoice:
                                _logger.warning("%s Amount not found [%s]" % (
                                    counter, line))
                                continue # Could happen

                            # Not classified (TODO but imported, true?!?!)
                            if not (month or year): 
                                _logger.error("%s Month/Year not found! %s" % (
                                    counter, line))

                            # OC old = today
                            if (type_document == 'oc') and ("%s%02d" % (
                                    year, month) < datetime.now().strftime(
                                        "%Y%m")):
                                _logger.warning(
                                    "%s) Old OC > today: %s%02d, cliente: %s, "
                                    "totale %s" % (
                                        counter, year, month, mexal_id, 
                                        total_invoice))
                                year = datetime.now().strftime("%Y")
                                month = int(
                                    datetime.now().strftime("%m"))

                            data = {
                                "name": "%s [%s]" % (partner_name, mexal_id),
                                "partner_id": partner_id,
                                "month": month,
                                "type_document": type_document,
                                }

                            # Year to intert invoiced 
                            year_month = "%s%02d" % (year, month)

                            current_year = int(
                                datetime.now().strftime("%Y"))
                            current_month = int(
                                datetime.now().strftime("%m"))
                                
                            # Season 
                            if current_month >= 1 and current_month <= 8:
                                ref_year = current_year - 1 
                            elif current_month >= 9 and current_month <= 12:
                                ref_year = current_year
                            else:
                                _logger.error("%s) Month error not [1:12]" % (
                                    counter))

                            # september - current year >> agoust - next year
                            if year_month >= "%s09" % ref_year and \
                                    year_month <= "%s08" % (
                                        ref_year + 1, ): # current
                                data['total'] = total_invoice
                            elif year_month >= "%s09" % (
                                    ref_year -1, ) and \
                                    year_month <= "%s08" % (
                                        ref_year, ): # year -1
                                data['total_last'] = total_invoice
                            elif year_month >= "%s09" % (
                                    ref_year -2, ) and \
                                    year_month <= "%s08" % (
                                        ref_year -1, ): # year -2
                                data['total_last_last'] = total_invoice
                            elif year_month >= "%s09" % (
                                    ref_year -3, ) and \
                                    year_month <= "%s08" % (
                                        ref_year -2, ): # year -3
                                data['total_last_last_last'] = total_invoice
                            elif year_month >= "%s09" % (
                                    ref_year -4, ) and \
                                    year_month <= "%s08" % (
                                        ref_year -3, ): # year -4
                                data['total_last_last_last_last'] = \
                                    total_invoice
                            else:
                                continue # jump

                            try:
                                # Common part (correct + amount)
                                invoice_id = self.create(
                                    cr, uid, data, context=context)
                                if step == 2: # Second payment negative! 
                                    # invert sign and setup agent
                                    data['name'] = "%s [%s]" % (
                                        partner_name2, mexal_id2)
                                    data['partner_id'] = partner_id2
                                    data['total'] = -data.get(
                                        'total', 0.0)
                                    data['total_last'] = -data.get(
                                        'total_last', 0.0)
                                    data['total_last_last'] = -data.get(
                                        'total_last_last', 0.0)
                                    data['total_last_last_last'] = -data.get(
                                        'total_last_last_last', 0.0)
                                    data['total_last_last_last_last'] = \
                                        -data.get(
                                            'total_last_last_last_last', 0.0)
                                    invoice_id = self.create(
                                        cr, uid, data, context=context)
                            except:
                                _logger.error("%s Error create invoice: %s" % (
                                    counter, mexal_id))
                        except:
                            _logger.error("%s Error import invoice: [%s]" % (
                                counter, sys.exc_info()))
                    
                _logger.info("Statistic invoice import terminated")
            # -----------------------------------------------------------------
            #                      STATISTIC.TREND IMPORT
            # -----------------------------------------------------------------
            # Common part:
            for documento in ('oc', 'ft', 'bc'):
                # Invoice and OC + Invoice
                _logger.info("Compute statistic.trend %s" % documento)
                if documento == "ft": # Solo fatture
                    invoice_ids = self.search(cr, uid, [
                        ('type_document','=','ft')], context=context)
                else: # all oc + ft + bc
                    invoice_ids = self.search(cr, uid, [], context=context)

                if invoice_ids: # Delete previous
                    if documento == "ft":
                       trend_ids = trend_pool.search(
                           cr, uid, [], context=context)
                       trend_pool.unlink(cr, uid, trend_ids, context=context)
                    else:
                       trendoc_ids = trendoc_pool.search(
                           cr, uid, [], context=context)
                       trendoc_pool.unlink(
                           cr, uid, trendoc_ids, context=context)

                    # Load list value for all partner
                    item_list = {}
                    # NOTE: add after so no correct order: 
                    total_invoiced = [0.0, 0.0, 0.0, 0.0, 0.0] # -2 -1 0 -4 -3
                    for item in self.browse(
                            cr, uid, invoice_ids, context=context):
                        partner_id = item.partner_id and item.partner_id.id \
                            or False

                        if partner_id not in item_list:
                            # stesso discorso per l'aggiunta a posteriori
                            item_list[partner_id] = [0.0, 0.0, 0.0, 0.0, 0.0]

                        if item.total: #current
                            item_list[partner_id][2] += item.total
                            total_invoiced[2] += item.total
                        if item.total_last: # year -1
                            item_list[partner_id][1] += item.total_last
                            total_invoiced[1] += item.total_last
                        if item.total_last_last: # year -2
                            item_list[partner_id][0] += item.total_last_last
                            total_invoiced[0] += item.total_last_last
                        if item.total_last_last_last: # year -3
                            item_list[partner_id][3] += \
                                item.total_last_last_last
                            total_invoiced[3] += item.total_last_last_last
                        if item.total_last_last_last_last: # year -4
                            item_list[partner_id][4] += \
                                item.total_last_last_last_last
                            total_invoiced[4] += item.total_last_last_last_last

                _logger.info("Add statistic archive for %s" % documento)
                for elemento_id in item_list.keys(): # for % calculate
                    data = {
                        'name': "cliente: %d" % elemento_id,
                        'partner_id': elemento_id,
                        'total': item_list[elemento_id][2],
                        'total_last': item_list[elemento_id][1],
                        'total_last_last': item_list[elemento_id][0],
                        'total_last_last_last': item_list[elemento_id][3],
                        'total_last_last_last_last': item_list[elemento_id][4],
                        'percentage': (total_invoiced[2]) and (
                            item_list[elemento_id][2] * 100 / (
                                total_invoiced[2])), # current year
                        'percentage_last': (total_invoiced[1]) and (
                            item_list[elemento_id][1] * 100 / (
                                total_invoiced[1])), # -1 year
                        'percentage_last_last': (total_invoiced[0]) and (
                            item_list[elemento_id][0] * 100 / (
                                total_invoiced[0])), # -2 year
                        # percentage_last_last_last
                        # percentage_last_last_last_last
                        }
                    try:
                       if documento == "ft":
                          trend_id = trend_pool.create(
                              cr, uid, data, context=context)
                       else:
                          trend_id = trendoc_pool.create(
                              cr, uid, data, context=context)
                    except:
                        _logger.error("Error create order for partner: %s" % (
                           elemento_id))
        except:
            _logger.error("Error import order")

        return True
        
    _columns = {
        'name': fields.char('Descrizione', size=64),
        'visible': fields.boolean('Visible',),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'invoice_agent_id': fields.related('partner_id','invoice_agent_id',
            type='many2one', relation='statistic.invoice.agent',
            string='Invoice agent'),
        'hide_statistic': fields.related('invoice_agent_id','hide_statistic',
            type='boolean', string='Nascondi statistica'),
        'type_cei': fields.related('partner_id','type_cei', type='char',
            size=1, string='C E I'),
        'total': fields.float('Stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Stag. -1', digits=(16, 2)),
        'total_last_last': fields.float('Stag. -2', digits=(16, 2)),
        'total_last_last_last': fields.float('Stag. -3', digits=(16, 2)),
        'total_last_last_last_last': fields.float('Stag. -4', digits=(16, 2)),
        'season_total': fields.char(
            'Totale', size=15,
            help='Only a field for group in graph total invoice'),
        'type_document': fields.selection([
            ('ft', 'Fattura'),
            ('oc', 'Ordine'),
            ('bc', 'DDT'),
            ], 'Tipo doc.', select=True),
        'month': fields.selection([
            (0, '00 Non trovato'),
            (1, 'Mese 05*: Gennaio'),
            (2, 'Mese 06*: Febbraio'),
            (3, 'Mese 07*: Marzo'),
            (4, 'Mese 08*: Aprile'),
            (5, 'Mese 09*: Maggio'),
            (6, 'Mese 10*: Giugno'),
            (7, 'Mese 11*: Luglio'),
            (8, 'Mese 12*: Agosto'),
            (9, 'Mese 01: Settembre'),
            (10, 'Mese 02: Ottobre'),
            (11, 'Mese 03: Novembre'),
            (12, 'Mese 04: Dicembre'),
            ],'Mese', select=True),
        'trend': fields.related('partner_id', 'trend', type='boolean',
            readonly=True, string='Important partner'),

        # Extra info for filter graph:
        'zone_id': fields.related('partner_id','zone_id', type='many2one',
            relation='res.partner.zone', string='Zone', store=True),
        'zone_type': fields.related('zone_id','type', type='selection',
            selection=[
                ('region', 'Region'), ('state', 'State'), ('area', 'Area'),
                ], string='Tipo', store=True),
        'country_id': fields.related('partner_id', 'country_id', 
            type='many2one', relation='res.country', string='Country', 
            store=True),
        }

    _defaults = {
        'total': lambda *a: 0.0,
        'total_last': lambda *a: 0.0,
        'total_last_last': lambda *a: 0.0,
        'total_last_last_last': lambda *a: 0.0,
        'total_last_last_last_last': lambda *a: 0.0,
        'season_total': lambda *a: 'Totale', # always the same
        'visible': lambda *a: False,
        }

class StatisticInvoiceProduct(orm.Model):
    ''' Statistic on product:
        Partner - month - product = key
    '''
    _name = 'statistic.invoice.product'
    _description = 'Statistic invoice'
    _order = 'month, name'

    def schedule_csv_statistic_invoice_product_import(self, cr, uid, 
            input_file, delimiter=';', header=0, verbose=100, context=None):
        ''' Schedule procedure for import statistic.invoice.product
        '''    
        # TODO for log check:
        #create_date=time.ctime(os.path.getctime(FileInput))    
        import pdb; pdb.set_trace()
        _logger.info("Start importation product invoice stats: %s" % (
            input_file))    
        lines = csv.reader(open(input_file, 'rb'), delimiter=delimiter)
        counter = -header

        item_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, item_ids, context=context)

        tot_col=0
        season_total = 0 
        item_invoice = {}
        try:
            for line in lines:
                if tot_col == 0: # save total cols
                   tot_col = len(line)
                   _logger.info("Total cols %s" % tot_col)
                if counter < 0:
                    counter += 1
                    continue

                if (len(line) and (tot_col == len(line))): 
                    _logger.warning("%s) Empty line or column err [%s>%s]" % (
                        counter, tot_col, len(line)))
                    counter += 1
                    continue
                try:                    
                    name = csv_base.decode_string(line[0]) # Family
                    month = int(csv_base.decode_string(line[1])) or 0
                    year = csv_base.decode_string(line[2])
                    total_invoice = csv_base.decode_float(line[3]) or 0.0
                    type_document = csv_base.decode_string(line[4]).lower()
                                                                  
                    # Calculated field:
                    if type_document not in ('ft', 'bc', 'oc'):
                        _logger.warning("%s) Type of doc not correct: %s" % (
                            counter, type_document)) 
                        type_document = False
                          
                        data = {
                            "name": name, 
                            "month": month, 
                            "type_document": type_document,
                            }
             
                        # Which year
                        if not (year or month): 
                            _logger.error("%s) Year %s or month %s not found" % (
                                counter, year, month)) 

                        year_month = "%s%02d" % (year, month)                        
                        current_year = int(datetime.now().strftime("%Y"))
                        current_month = int(datetime.now().strftime("%m"))
                       
                        if current_month >=1 and current_month <=8:
                            ref_year = current_year - 1
                        elif current_month >= 9 and current_month <= 12:
                            ref_year = current_year  
                        else:
                            _logger.error("%s) Month error" % counter) 

                        # TODO: add also OC
                        if year_month >= "%s09" % ref_year and \
                                year_month <= "%s08" % (ref_year + 1):
                            data['total'] = total_invoice
                        elif year_month >= "%s09" % (ref_year -1) and \
                               year_month <= "%s08" % ref_year: # year-1
                            data['total_last'] = total_invoice
                        elif year_month >= "%s09" % (ref_year -2) and \
                                year_month <= "%s08" % (ref_year -1): #-2
                           data['total_last_last'] = total_invoice
                        else:  
                            _logger.warning("%s) Extra period %s-%s" % (
                                counter, year, month)) 
                        season_total += total_invoice
 
                        # Sum total for element
                        if name not in item_invoice:
                            item_invoice[name] = total_invoice
                        else:    
                            item_invoice[name] += total_invoice
                          
                        try:                      
                           invoice_id = self.create(
                               cr, uid, data, context=context)
                        except:
                            _logger.error("%s) Error create record" % counter)

                except:
                    _logger.error("%s) Error create record [%s]" % (
                       counter, sys.exc_info()))
                   
        except:
            _logger.error("%s) Error create record [%s]" % (
                counter, sys.exc_info()))
        _logger.info(
            "End importation records, start totals for split elements")

        try: # Split product depend on invoiced
            # Remove some code:
            remove_pool = self.pool.get('statistic.invoice.product.removed')
            item_ids = remove_pool.search(cr, uid, item_ids, context=context)
            product_removed = [
                item.name for item in remove_pool.browse(cr, uid, item_ids, 
                    context=context)]
            
            most_popular = []
            for family in item_invoice.keys():
                perc_invoice = item_invoice[
                    family] / season_total
                if perc_invoice >= 0.005: # 0,5% all 3 season
                    # Write element
                    if family not in product_removed and family \
                            not in most_popular:
                        most_popular.append(family)
                
            product_item_to_show_ids = self.search(cr, uid, [
                ('name', 'in', most_popular)], context=context)
            product_updated_percentile = self.write(
                cr, uid, product_item_to_show_ids, {
                    'visible': True}, context=context)
            _logger.info("Set top elements")

        except:
            _logger.error("%s) Error create record [%s]" % (
                counter, sys.exc_info()))
        
        return True
        
    _columns = {
        'name': fields.char('Famiglia prodotto', size=64),
        'visible': fields.boolean('Visible',), ## used!
        'total': fields.float('Stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Stag. -1', digits=(16, 2)),
        'total_last_last': fields.float('Stag. -2', digits=(16, 2)),

        'percentage': fields.float(
            '% sul fatt. stag. corrente', digits=(16, 5)),
        'percentage_last': fields.float(
            '% sul fatt. stag. -1', digits=(16, 5)),
        'percentage_last_last': fields.float(
            '% sul fatt. stag. -2', digits=(16, 5)),

        'type_document': fields.selection([
            ('ft','Fattura'),
            ('oc','Ordine'),
            ('bc','DDT'),
            ], 'Tipo doc.', select=True), # togliere?
        'month': fields.selection([
            (0, '00 Non trovato'),
            (1, 'Mese 05*: Gennaio'),
            (2, 'Mese 06*: Febbraio'),
            (3, 'Mese 07*: Marzo'),
            (4, 'Mese 08*: Aprile'),
            (5, 'Mese 09*: Maggio'),
            (6, 'Mese 10*: Giugno'),
            (7, 'Mese 11*: Luglio'),
            (8, 'Mese 12*: Agosto'),
            (9, 'Mese 01: Settembre'),
            (10, 'Mese 02: Ottobre'),
            (11, 'Mese 03: Novembre'),
            (12, 'Mese 04: Dicembre'),
        ],'Mese', select=True),
        }

    _defaults = {
        'total': lambda *a: 0.0,
        'total_last': lambda *a: 0.0,
        'total_last_last': lambda *a: 0.0,
        #'total_last_last_last': lambda *a: 0.0,
        #'total_last_last_last_last': lambda *a: 0.0,
        'visible': lambda *a: False,
    }

class StatisticInvoiceProductRemoved(orm.Model):
    ''' Product not present in statistic
    '''
    _name = 'statistic.invoice.product.removed'
    _description = 'Statistic Product to remove'

    _columns = {
        'name': fields.char(
            'Famiglia', size = 64, required=True),
        }
    
class ResPartnerStatistic(orm.Model):
    """ res_partner_extra_fields
    """
    _inherit = 'res.partner'

    _columns = {
        'trend': fields.boolean(
            'Trend',
            help="Insert in trend statistic, used for get only interesting "
                "partner in statistic graph"),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
