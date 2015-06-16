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


class StatisticCategory(orm.Model):
    """ Statistic category 
    """
    
    _name = 'statistic.category'
    _description = 'Statistic category'

    _columns = {
        'name': fields.char('Description', size=64),
        'trend': fields.boolean('Trend'),
    }

    _defaults = {
        'trend': lambda *a: False,
    }

class ResPartnerStatistic(orm.Model):
    """ res_partner_extra_fields
    """
    _inherit = 'res.partner'

    _columns = {
        'statistic_category_id': fields.many2one(
            'statistic.category', 'Statistic category',
            help='Valore di categoria statistica acquisito dal gestionale'),
        'trend_category': fields.related(
            'statistic_category_id', 'trend', type='boolean',
            string='Trend category',
            help='Indica se la categoria è rappresentata nel grafico trend',
            readonly=True),

        'saldo_c': fields.float('Customer balance', digits=(16, 2)),
        'saldo_s': fields.float('Supplier balance', digits=(16, 2)),

        'ddt_e_oc_c': fields.float(
            'Customer balance OC+DDT opened', digits=(16, 2)),
        'ddt_e_oc_s': fields.float(
            'Supplier balance OC+DDT opened', digits=(16, 2)),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
