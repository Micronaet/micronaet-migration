# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
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

class StatisticStore(orm.Model):
    ''' Object that store data from 2 company for mix store values
        using protocol to link product from Company 1 to Company 2
    '''

    _name = 'statistic.store'
    _description = 'Store info'
    _rec_name = "product_code"
    _order = "product_code,product_description"

    _columns = {
        # Extra info calculated:
        'company':fields.selection([
                ('gpb','G.P.B.'),
                ('fia','Fiam'),
                ], 'Company', select=True),

        # Product info:
        'mexal_s': fields.char('Mexal ID', size=10),
        'supplier': fields.char('Supplier', size=68),
        'product_code': fields.char('Product code', size=24),
        'q_x_pack': fields.integer('Q. x pack'),
        'product_description': fields.char('Product description', size=128),
        'product_um': fields.char('UOM', size=4),

        # Value fields
        'inventary': fields.float('Inventary', digits=(16, 2)),
        'q_in': fields.float('In', digits=(16, 2)),
        'q_out': fields.float('Out', digits=(16, 2)),
        'balance': fields.float('Existent', digits=(16, 2)),
        'supplier_order': fields.float('OF', digits=(16, 2)),
        'customer_order': fields.float('OC imp.', digits=(16, 2)),
        'customer_order_auto': fields.float(
            'OC automatic in prod.', digits=(16, 2)),
        'customer_order_suspended': fields.float(
            'OC suspended', digits=(16, 2)),

        # Field calculated:
        'disponibility': fields.float('Dispo lord', digits=(16, 2)),
        'product_um2': fields.char('UM2', size=4),
        'inventary_last': fields.float('Manual inventary', digits=(16, 2)),

        'both': fields.boolean('Entrambe',
            help="Esiste in entrambe le aziende"),
        }

    _defaults = {
        'both': lambda *a: False,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
