# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
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
import base64, urllib


_logger = logging.getLogger(__name__)



class BaseContainerType(orm.Model):
    '''Type of Container: type of container used for standard total cost
       used for divide for tot article to part cost on unit
    '''
    _name = 'base.container.type'
    _description = 'Container type'

    _columns = {
        'name': fields.char('Container', size=40, required=True),
        'cost': fields.float('Loan cost (EUR)', digits=(16, 2)),
        'date': fields.date('Date of quotation'),
        }

    _defaults = {
        'cost': lambda *x: 0.0,
        'date': lambda *a: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

class ProductPackagingFunction(orm.Model):
    '''Add extra fields for
    '''
    _inherit = 'product.packaging'

    # fields function
    def _function_get_volume(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pack in self.browse(cr, uid, ids, context=context):
            res[pack.id] = (
                pack.length or 0 * pack.width or 0 * pack.height or 0
                ) / 1000000 # TODO approx
        return res

    def _function_get_transport(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pack in self.browse(cr, uid, ids, context=context):
            try:
               res[pack.id] = round((
                   pack.container_id and pack.container_id.cost or 0) / (
                       pack.q_x_container or 0),2)
            except: # division by zero!
               res[pack.id] = 0.00
        return res


    _columns = {
        'container_id': fields.many2one(
            'base.container.type', 'Container type', ondelete="set null"),
        'q_x_container': fields.integer('Q. x container'),
        'transport_cost': fields.function(
            _function_get_transport, method=True, type='float',
            string='Transport cost unit (EUR)', store=False),

        'dimension_text': fields.text('Dimension (textual)'), # TO DELETE
        'error_dimension_pack': fields.boolean('Error dimens. pack'), # TO DEL.

        'pack_volume': fields.float('Pack volum (manual)', digits=(16, 3)),
        'pack_volume_manual': fields.boolean('Manual volum'),
        }

    _defaults = {
        'q_x_container': lambda *x: 0,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
