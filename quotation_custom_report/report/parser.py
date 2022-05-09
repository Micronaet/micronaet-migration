##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.counters = {}
        self.localcontext.update({
            # Company2:
            'get_partner_address': self.get_partner_address,
            'get_partner_return_info': self.get_partner_return_info,
            'get_item_photo_context': self.get_item_photo_context,

            # Company 1:
            'clean_description': self.clean_description,
            'get_telaio': self.get_telaio,
            'get_fabric': self.get_fabric,
            'get_fabric_description': self.get_fabric_description,
            'set_counter': self.set_counter,
            'get_counter': self.get_counter,

            'get_total_volume': self.get_total_volume,
            'total_volume': self.total_volume,

            # TODO remove
            'temp_get_order': self.temp_get_order,
        })

    def get_partner_address(self, order):
        """ Return format destination address or current address
        """
        if order.destination_partner_id: # destination address
            partner = order.destination_partner_id
        else:  # partner address
            partner = order.partner_id
        return '%s\n%s %s %s %s' % (
            partner.name,
            partner.street or '',
            partner.zip or '',
            partner.city or '',
            partner.country_id.name or '',
            )

    def get_partner_return_info(self, order):
        """ Extra data for return goods
        """
        if (order.partner_id.lang or 'en_US') == 'en_US':
            mask = 'Delivery terms: %s\nPayment terms: %s'
        else:
            mask = 'Resa merce: %s\nPagamento: %s'
        return mask % (
            order.return_id.text or '',
            order.payment_term.name or '',
            )

    def get_item_photo_context(self, o):
        """ Update context for load particular photo
        """
        order_pool = self.pool.get('sale.order')
        cr = self.cr
        uid = self.uid
        context = {'album_code': 'QUOTATION', }

        return order_pool.browse(cr, uid, o.id, context=context).order_line

    def get_total_volume(self, order_line):
        """ Function that compute total volume for 1 or more items
        """
        total = 0.0
        for item in order_line:
            product = item.product_id
            if not product.q_x_pack:
                continue

            if product:
                total += item.product_uom_qty * (
                    product.pack_l * product.pack_h * product.pack_p /
                    1000000.0) / product.q_x_pack
        return '%2.2f' % total

    def total_volume(self, order_id):
        """ calculate total volume for all items present in order
        """
        # item_list = self.pool.get('purchase.order').browse(
        #    self.cr, self.uid, order_id).order_line
        # if item_list:
        #    return self.get_total_volume([item.id for item in item_list])
        return ''

    def temp_get_order(self):
        pool = self.pool.get('product.product')
        item_ids = pool.search(self.cr, self.uid, [])
        return pool.browse(self.cr, self.uid, item_ids)

    def set_counter(self, name, value=0.0):
        """ Create or set a counter in the counter list of the class
            If value is not set counter is reset
        """
        self.counters[name] = value
        return

    def get_counter(self, name):
        """ Return counter value, if present, else 0.0
        """
        return self.counters.get(name, 0.0)

    def clean_description(self, name):
        return name.split("]")[-1:]

    def get_fabric_description(self, product):
        """ Return correct description depend on code
            (write only for TS TL MS TS PO
        """
        if not product:
            return ''
        default_code = product.default_code
        if default_code[:2].upper() in ('TL', 'TS', 'MT', 'MS', 'PO'):
            return u' %s' % (product.fabric or '')
        return ''

    def get_fabric(self, code, language):
        """ Return type of fabric depend on start code
        """
        code = code.upper()
        if code[3:6] == "TXI":
            if language == 'it_IT':
                return "Texfil ignifugo"
            else:
                return "Texfil fire retardant"

        elif code[3:6] == "TXR" or code[3:5] == "TX":
            if language == 'it_IT':
                return "Texfil"
            else:
                return "Texfil"

        elif code[3:5] == "PE":
            if language == 'it_IT':
                return "Poliestere"
            else:
                return "Polyester"

        elif code[3:5] == "S3":
            if language == 'it_IT':
                return "Triplex"
            else:
                return "Triplex"

        elif code[3:5] == "SB" or code[3:4] == "S":
            if language == 'it_IT':
                return "Olefine"
            else:
                return "Olefine"

        elif code[3:4] == "L" or code[3:5] == "IL":
            if language == 'it_IT':
                return "Acrypol"
            else:
                return "Acrypol"

        else:
            _logger.error('Errore recuperando il codice: [%s]' % code)
            return "/"

    def get_telaio(self, name, lingua):
        """ Last minute function for convert name (not translated in product)
        """
        name = name.strip()
        if not name:
            return ""

        # If name is originally in english translate in italian
        if name == "STEEL":
           name = "ACCIAIO"
        elif name == "WOOD":
           name = "LEGNO"
        elif name == "WOODEN":
           name = "LEGNO"
        elif name == "IRON PAINTED":
           name = "TINTO FERRO"
        elif name == "IRON CHROMED":
           name = "CROMATO FERRO"
        elif name == "ANODIZED ALUMINIUM":
           name = "ALLUMINIO ANODIZZATO"
        elif name == "ALUMINIUM":
           name = "ALLUMINIO"
        elif name == "IRON":
           name = "FERRO"
        elif name == "WALNUT":
           name = "NOCE"

        ita2eng = {
           "ALLUMINIO": "ALUMINIUM",
           "LEGNO": "WOOD",
           "ACCIAIO": "STEEL",
           "TINTO NOCE": "PAINTED WALNUT",
           "NOCE": "WALNUT",
           "ALLUMINIO ANODIZZATO": "ANODIZED ALUMINIUM",
           "CROMATO FERRO": "IRON CHROMED",
           "TINTO FERRO": "IRON PAINTED",
           "FERRO": "IRON",
           "ROBINIA": "ROBINIA",
           }
        if lingua == 'it_IT':
            return name
        else:
            _logger.error('Errore telaio recuperando: [%s]' % name)
            return ita2eng[name] if name in ita2eng else "?"
