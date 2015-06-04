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

class ProductProductQuotation(orm.Model):
    """ product.product extra fields
    """
    _inherit = 'product.product'

    _columns = {
        'telaio': fields.char('Telaio', size=64,
            translate=True),
        'pipe_diameter':fields.char(
            'Diam. tubo', size=15),
        'weight_packaging':fields.char('Peso imballo', size=20),
        'item_per_box':fields.char('Pezzi per scatola', size=20),
        'item_per_pallet':fields.char('Pezzi per bancale', size=20),
        'item_per_mq':fields.char('Pezzi per metro cubo', size=20),
        'item_per_camion':fields.char('Pezzi per camion 13,6 mt.', size=20),

        'extra_description':fields.text('Extra description', translate=True),

        # Non visibili attualmente nella vista
        'dim_article':fields.char('Dim. art.', size=20),
        'dim_pack':fields.char('Dim. scatola', size=20),
        'dim_pallet':fields.char('Dim. pallet', size=20),
        }

class SaleOrderQuotation(orm.Model):
    """ sale.order extra fields
    """
    _inherit = 'sale.order'

    _columns = {
        'quotation_model': fields.selection([
            (1, 'Offerta dettagliata (q.-sconto-subtotali)'),
            (2, 'Offerta breve (solo q.)'),
            ], 'Model'),
        'destination_partner_id': fields.many2one(
            'res.partner', 'Destination'),     
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
        }
