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


class statistic_deadline(orm.Model):
    _name = 'statistic.deadline'
    _description = 'Statistic deadline'
    _order = 'name,deadline' # name is loaded with partner name during import

    _columns = {
        'name': fields.char('Deadline', size=64),
        'visible': fields.boolean('Visible',),

        'partner_id': fields.many2one('res.partner', 'Partner'),
        'property_account_position': fields.related(
            'partner_id', 'property_account_position', type='many2one',
            relation='account.fiscal.position', store=True,
            string='Fiscal position'),
        'c_o_s': fields.char('Cl. o For.', size=1),
        'deadline': fields.date('Dead line'),

        'fido_date': fields.related(
            'partner_id', 'fido_date', type="date", string="Data fido"),
        'fido_ko': fields.related(
            'partner_id', 'fido_ko', type="boolean", string="Fido concesso"),
        'fido_total': fields.related(
            'partner_id', 'fido_total',  type="float", digits=(16, 2),
            string="Importo fido"),

        'total': fields.float('Total', digits=(16, 2)),
        'in': fields.float('Entrate', digits=(16, 2)),
        'out': fields.float('Uscite', digits=(16, 2)),

        # Non fatto related ma calcolato al volo
        'scoperto_c':  fields.float('Scoperto cliente', digits=(16, 2)),
        'scoperto_s':  fields.float('Scoperto fornitore', digits=(16, 2)),

        'saldo_c': fields.related(
            'partner_id', 'saldo_c', type='float', digits=(16, 2),
            string='Saldo (cliente)'),
        'saldo_s': fields.related(
            'partner_id', 'saldo_s', type='float', digits=(16, 2),
            string='Saldo (fornitore)'),

        'ddt_e_oc_c': fields.related(
            'partner_id', 'ddt_e_oc_c', type='float', digits=(16, 2),
            string='DDT + OC aperti (cliente)'),
        'ddt_e_oc_s': fields.related(
            'partner_id', 'ddt_e_oc_s', type='float', digits=(16, 2),
            string='DDT + OC aperti (fornitore)'),

        'type': fields.selection([
            ('b','Bonifico'),
            ('c','Contanti'),
            ('r','RIBA'),
            ('t','Tratta'),
            ('m','Rimessa diretta'),
            ('x','Rimessa diretta X'),
            ('y','Rimessa diretta Y'),
            ('z','Rimessa diretta Z'),
            ('v','MAV'),
        ], 'Type', select=True),
    }
    _defaults = {
        'total': lambda *a: 0,
        'in': lambda *a: 0,
        'out': lambda *a: 0,
        'scoperto_c': lambda *a: 0,
        'scoperto_s': lambda *a: 0,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
