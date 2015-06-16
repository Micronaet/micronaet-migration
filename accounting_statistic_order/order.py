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
            'partner_id', 'country', type='many2one',
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

    _order='deadline, name'
    _description = 'Testate ordini'

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
            'partner_id', 'country', type='many2one', relation='res.country',
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
