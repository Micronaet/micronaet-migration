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
    # Importation procedure (scheduled):
    # ----------------------------------
    def schedule_csv_statistic_invoice_import(self, cr, uid,
            file_input1='~/ETL/fatmeseoerp1.csv',
            file_input2='~/ETL/fatmeseoerp2.csv',
            delimiter=';', header=0, verbose=100, 
            particular=True, context=None):
        """ Import statistic data from CSV file for invoice, trend, trendoc
            This particular importation are from 2 files (amount)
            (all particularity manage are use if particular = True)
        """

        _logger.info('Start invoice statistic for customer')

        # File CSV date for future log
        #create_date=time.ctime(os.path.getctime(FileInput))

        # statistic.invoice:
        sql_pool = self.pool.get('micronaet.accounting')
        csv_base = self.pool.get('csv.base')
        invoice_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, invoice_ids, context=context)

        # Load dict for swap destination in parent ID
        _logger.info('Read parent for destinations conversion')
        convert_destination = {}
        cursor = sql_pool.get_parent_partner(cr, uid, context=context)
        if not cursor:
            _logger.error("Unable to connect to parent (destination)!")
            return False # Fatal error!
        else:
            for record in cursor:
                convert_destination[record['CKY_CNT']] = record[
                    'CKY_CNT_CLI_FATT']

        # Load tags for create a dict of partner:
        partner_tags = {}
        tag_pool = self.pool.get('res.partner.category')
        tag_ids = tag_pool.search(cr, uid, [
            ('statistic', '=', True)], context=context)        
        for tag in tag_pool.browse(cr, uid, tag_ids, context=context):
            for partner in tag.partner_ids:
                partner_tags[partner.id] = tag.id # TODO problem in multi pres.

        # TODO portare parametrizzandolo in OpenERP (second loop substitution):
        # =====================================================================
        if particular:
            p1_id = csv_base.get_create_partner_lite(
                cr, uid, '06.02209', context=context)
            p2_id = csv_base.get_create_partner_lite(
                cr, uid, '06.01537', context=context)
            customer_replace = {
                '06.40533': (
                    ('06.02209', p1_id, get_partner_name(
                        self, cr, uid, p1_id)),
                    ('06.01537', p2_id, get_partner_name(
                        self, cr, uid, p2_id)),
                    )}
        # =====================================================================

        loop_steps = { # 2 loop for read the 2 files to mix
            1: csv.reader(
                open(os.path.expanduser(file_input1), 'rb'),
                delimiter=delimiter),
            }
        if particular:
            loop_steps[2] = csv.reader(
                open(os.path.expanduser(file_input2), 'rb'),
                delimiter=delimiter)

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
                        month_season = transcode_month[month]
                        year = csv_base.decode_string(line[2]) or ''
                        total_invoice = csv_base.decode_float(
                            line[3]) or 0.0
                        type_document = csv_base.decode_string(
                            line[4]).lower() # oc/ft

                        if particular and step == 2: # 2nd loop is different:
                            if mexal_id not in customer_replace:
                                continue # jump if not a replace partner

                            # =============================================
                            # Customer replace problem:
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
                            # =============================================

                        elif particular: # 1st loop is different:
                            # TODO parametrizable with destination switch?
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
                                    '%s: replace code: %s > 06.03044' % (
                                        counter, mexal_id))
                                mexal_id = '06.03044'
                        # Calculated field:
                        partner_id = csv_base.get_create_partner_lite(
                            cr, uid, mexal_id, context=context)
                        if not partner_id:
                            _logger.error(
                                '%s) Partner not found: %s' % (
                                counter, mexal_id))
                            partner_name = '#ERR Partner code %s' % (
                                mexal_id or '')
                        else:
                            partner_name = get_partner_name(
                                self, cr, uid, partner_id)

                        if not total_invoice:
                            _logger.warning('%s Amount not found [%s]' % (
                                counter, line))
                            continue # Considered and error, jumped

                        # Not classified (TODO but imported, true?!?!)
                        if not (month or year):
                            _logger.error('%s Month / Year not found! %s' % (
                                counter, line))

                        # OC old = today
                        if (type_document == 'oc') and ('%s%02d' % (
                                year, month) < datetime.now().strftime(
                                    '%Y%m')):
                            _logger.warning(
                                '%s) Old OC > today: %s%02d, cliente: %s, '
                                'totale %s' % (
                                    counter, year, month, mexal_id,
                                    total_invoice))
                            year = datetime.now().strftime('%Y')
                            month = int(datetime.now().strftime('%m'))

                        data = {
                            'name': '%s [%s]' % (partner_name, mexal_id),
                            'partner_id': partner_id,
                            'tag_id': partner_tags.get(partner_id, False),
                            'month': month_season, # month,
                            'type_document': type_document,
                            'year': year,
                            'total': total_invoice,
                            }

                        # Year to intert invoiced
                        year_month = '%s%02d' % (year, month)

                        current_year = int(datetime.now().strftime('%Y'))
                        current_month = int(datetime.now().strftime('%m'))

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
                        elif year_month >= '%s09' % (
                                ref_year -1, ) and \
                                year_month <= '%s08' % (
                                    ref_year, ): # year -1
                            data['season'] = -1
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
                            if year_month > '%s08':
                                data['season'] = 100 # new season
                            else:
                                data['season'] = -100 # old season

                        # Common part (correct + amount)
                        self.create(cr, uid, data, context=context)
                        if step == 2: # Second payment negative!
                            # invert sign and setup agent
                            data['name'] = '%s [%s]' % (
                                partner_name2, mexal_id2)
                            data['partner_id'] = partner_id2
                            data['total'] = -data.get('total', 0.0)
                            self.create(cr, uid, data, context=context)
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
            ('oc', 'Ordine'),
            ('bc', 'DDT'), ], 'Tipo doc.', select=True),

        'month': fields.selection([
            (0, '00 Non trovato'),
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
            ], 'Mese', select=True),

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
                if type_document not in ('ft', 'bc', 'oc'):
                    _logger.warning('%s) Type of doc not correct: %s' % (
                        counter, type_document))
                    type_document = False # not jumperd

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
                current_year = int(datetime.now().strftime('%Y'))
                current_month = int(datetime.now().strftime('%m'))

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

        'month': fields.selection([
            (0, '00 Non trovato'),
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
            ], 'Month', select=True),
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
