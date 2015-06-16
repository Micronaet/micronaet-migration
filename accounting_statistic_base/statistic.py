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
            'statistic.category', 'Categoria statistica',
            help='Valore di categoria statistica acquisito dal gestionale'),
        'trend_category': fields.related(
            'statistic_category_id', 'trend', type='boolean',
            string='Categoria trend',
            help='Indica se la categoria è rappresentata nel grafico trend',
            readonly=True),

        'saldo_c': fields.float('Saldo cliente', digits=(16, 2)),
        'saldo_s': fields.float('Saldo fornitore', digits=(16, 2)),

        'ddt_e_oc_c': fields.float(
            'Saldo cliente OC+DDT aperti', digits=(16, 2)),
        'ddt_e_oc_s': fields.float(
            'Saldo fornitore OC+DDT aperti', digits=(16, 2)),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
