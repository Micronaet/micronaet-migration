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

        'total': fields.float('Tot. stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Tot. stag. -1', digits=(16, 2)),
        'total_last_last': fields.float('Tot. stag. -2', digits=(16, 2)),

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

class StatisticInvoice(orm.Model):
    _name = 'statistic.invoice'
    _description = 'Statistic invoice'
    _order = 'month, name'

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
        'country_id': fields.related('partner_id','country', type='many2one',
            relation='res.country', string='Country', store=True),
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
    _name = 'statistic.invoice.product'
    _description = 'Statistic invoice'
    _order = 'month, name'

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
