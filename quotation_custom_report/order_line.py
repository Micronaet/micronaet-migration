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
import base64
import urllib
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


class SaleOrderQuotation(orm.Model):
    """ sale.order extra fields
    """
    _inherit = 'sale.order'

    # Override fake wizard button event for print this report:
    def print_quotation(self, cr, uid, ids, context=None):
        ''' Override originaL function that prints the sales order and mark it 
            as sent, so that we can see more easily the next step of the 
            workflow
        '''
        assert len(ids) == 1, \
            'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'quotation_sent')
        return self.pool['report'].get_action(
            cr, uid, ids, 'fiam_order_report', context=context)

    _columns = {
        'quotation_model': fields.selection([
            (1, 'Offerta dettagliata (q.-sconto-subtotali)'),
            (2, 'Offerta breve (solo q.)'),
            ], 'Model'),
        }
    _defaults = {
        'quotation_model': lambda *x: 2, # short
        }

class SaleOrderLineQuotation(orm.Model):
    _inherit='sale.order.line'

    _columns={
        'insert_photo': fields.boolean(
            'Con foto',
            help="Spuntare quando e' richiesto l'inserimento della foto "
                "a preventivo."),
        'repeat_header_line': fields.boolean(
            'Intest.',
            help="Spuntare quando e' richiesta l'intestazione, tipo dopo una "
                "riga titolo."),
        'use_amazon_description': fields.boolean(
            'Amazon description',
            help="Take amazon description instead of product's one"),
        'show_notes': fields.boolean(
            'Show notes', help="Show notes after description"),
        'note': fields.text( 'Note'),    
        }
        
    _defaults = {
        'insert_photo': lambda *x: True,
        }
        
