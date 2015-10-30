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


_logger = logging.getLogger(__name__)

class ProductProductExtraFields(orm.Model):
    _inherit ='product.product'

    _columns = {
        'import': fields.boolean('Imported'),
        'mexal_id': fields.char(
            'Product mexal ID', size=20),
        'q_x_pack': fields.float(
            'Q. per collo', digits=(16, 3)),
        'linear_length': fields.float(
            'Lung. lineare', digits=(16, 3)),
        'large_description': fields.text(
            'Large Description', translate=True, help="For web publishing"),
        }

class ProductPricelistExtraFields(orm.Model):
    _inherit ='product.pricelist'

    _columns = {
        'import': fields.boolean('Imported', required=False),
        'mexal_id': fields.char(
            'Mexal Pricelist', size=9, required=False, readonly=False),
        }

class PricelistVersionExtraFields(orm.Model):
    _inherit ='product.pricelist.version'

    _columns = {
        'import': fields.boolean('Imported', required=False),
        'mexal_id': fields.char(
            'Mexal Pricelist version', size=9, required=False, readonly=False),
    }

class PricelistItemExtraFields(orm.Model):
    _inherit ='product.pricelist.item'

    _columns = {
        'mexal_id': fields.char(
            'Mexal Pricelist item', size=9, required=False, readonly=False),
    }

"""
# fiam_sale.py
Extra fields for object used in sale orders
Maybe this new objects are not necessary and will be replaced in the future
TODO Maybe discount part is better move in a single module
"""
class SaleOrderBank(orm.Model):
    _name = 'sale.order.bank'
    _description = 'Sale oder bank'

    _columns = {
        'name': fields.char('Bank account', size=64),
        'information': fields.text(
            'Information', translate=True,
            help="Account description, IBAN etc. linked in the offer"),
        }

class SaleProductReturn(orm.Model):
    ''' List of text sentences for the return of the product, this list are
        show in offer modules
    '''
    _name = 'sale.product.return'
    _description = 'Sale product return'

    _columns = {
        'name': fields.char('Description', size=64),
        'text': fields.text('Text', translate=True),
        }

class SaleOrderExtraFields(orm.Model):
    _inherit='sale.order'

    _columns = {
         'bank_id': fields.many2one('sale.order.bank', 'Conto bancario'),
         'print_address': fields.boolean('Use extra address'),
         'print_only_prices': fields.boolean('Only price offer'),
         'has_master_header': fields.boolean(
             'Header master table',
             help="In 'only comunication offer' doesn't add header"),
         'return_id': fields.many2one('sale.product.return', 'Product return'),
         }

    _defaults={
        'has_master_header': lambda *a: True,
        }

class SaleOrderLineExtraFields(orm.Model):
    _inherit ='sale.order.line'

    def create(self, cr, uid, vals, context=None):
        """ Multi discount rate
        """
        if not vals.get('discount', 0.0) and vals.get(
                'multi_discount_rates', False):
            res = self.on_change_multi_discount(
                cr, uid, 0, vals.get('multi_discount_rates'))['value']
            vals['discount'] = res.get('discount', '')
        return super(SaleOrderLineExtraFields, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """ Multi discount rate
        """
        if vals.get('multi_discount_rates', False):
            res = self.on_change_multi_discount(
                cr, uid, 0, vals.get('multi_discount_rates'))['value']
            vals['discount'] = res.get('discount', '')
        return super(SaleOrderLineExtraFields, self).write(
            cr, uid, ids, vals, context=context)

    def on_change_multi_discount(self, cr, uid, ids, multi_discount_rates, 
            context=None):
        ''' Get multidiscount return compute of discount and better format
            of multi rates
        '''
        res = {}
        if multi_discount_rates:
           disc = multi_discount_rates.replace(' ', '')
           disc = disc.replace(',', '.')
           discount_list = disc.split('+')
           if discount_list:
              base_discount = float(100)
              for aliquota in discount_list:
                  try:
                     i = float(eval(aliquota))
                  except:
                     i = 0.00
                  base_discount -= base_discount * i / 100.00
              res['discount'] = 100 - base_discount
              res['multi_discount_rates'] = '+ '.join(discount_list)
           else:
              res['discount'] = 0.0
              res['multi_discount_rates'] = ''
        else:
           res['discount'] = 0.00
           res['multi_discount_rates'] = ''
        return {'value': res}

    def _discount_rates_get(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('partner_id'):
           cr.execute("""
               SELECT discount_rates, id
               FROM res_partner
               WHERE id = %d
               """ % context['partner_id'])
           res = cr.fetchall()
           if res[0][0]:
              return res[0][0]
           else:
              return False
        else:
           return False

    def _discount_value_get(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('partner_id', False):
           cr.execute("""
               SELECT discount_value, id
               FROM res_partner
               WHERE id = %d""" % context['partner_id'])
           res = cr.fetchall()
           if res[0][0]:
              return res[0][0]
           else:
              return False
        else:
           return False

    _columns = {
        'multi_discount_rates': fields.char('Discount scale', size=30),
        'price_use_manual': fields.boolean('Use manual net price',
            help="If specificed use manual net price instead of "
                "lord price - discount"),
        'price_unit_manual': fields.float(
            'Manual net price', digits_compute=dp.get_precision('Sale Price')),
        'image_http': fields.boolean('Has image',
            help="Has link for image on the web"),
        'image_replace_name':fields.char('Override name',
            size=30,
            help="Usually the name is art. code + '.PNG', es. 400.PNG"
                "if you want to change write the name in this field!"),
               }
    _defaults = {
        'multi_discount_rates': _discount_rates_get,
        'discount': _discount_value_get,
        }

"""
# fiam_partner.py
Add zone manage TODO maybe better put in a single module
Add extra fields populated from accounting > maybe better in a single module
"""
class ResPartnerZone(orm.Model):
    _name = 'res.partner.zone'
    _description = 'Partner Zone'
    _order = 'type,name'

    _columns = {
        'name':fields.char('Zone', size=64, required=True),
        'mexal_id': fields.integer('Mexal ID'),
        'type': fields.selection([
            ('region', 'Region'),
            ('state', 'State'),
            ('area', 'Area'),
        ], 'Tipo', required=True),
    }
    _defaults = {
        'type': lambda *a: 'state',
    }

class ResPartnerExtraFields(orm.Model):
    _inherit ='res.partner'

    def _function_statistics_invoice(
            self, cr, uid, ids, args, field_list, context=None):
        '''
        Calculate up or down of invoice:
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: list of dictionary which contain partner id, colour
        '''
        if context is None:
           context = {}

        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            #import pdb; pdb.set_trace()
            if partner.invoiced_current_year == partner.invoiced_last_year:
               segno="equal"
               valore=0.0
            else:
               if partner.invoiced_last_year:
                  valore = 100.0 * (
                      partner.invoiced_current_year -
                      partner.invoiced_last_year) / partner.invoiced_last_year
               else:
                  valore = 100.0
               if partner.invoiced_current_year < partner.invoiced_last_year:
                  segno="down"
               else:
                  segno="up"

            res[partner.id] = {}
            res[partner.id]['invoice_trend'] = segno
            res[partner.id]['invoice_trend_perc'] = valore
        return res

    _columns = {
        'zone_id':fields.many2one('res.partner.zone', 'Zone'),
        'fido_date': fields.date('FIDO Date'),
        'fido_ko': fields.boolean('No FIDO'),
        'fido_total': fields.float('Totale fido', digits=(16, 2)),
        'mexal_note': fields.text('Mexal Note'),
        'import': fields.char('ID import', size=10),
        'mexal_c': fields.char('Mexal cliente', size=9),
        'mexal_s': fields.char('Mexal fornitore', size=9),
        'fiscal_id_code': fields.char('Fiscal code', size=16),
        'private': fields.boolean('Private'),
        'type_cei': fields.char('Type CEI', size=1),
        'discount_value': fields.float('Discount value', digits=(16, 2)),
        'discount_rates':fields.char('Discount scale', size=30),

        # Statistics values:
        'date_last_ddt': fields.datetime('Date last DDT'),
        'day_left_ddt': fields.integer('Day left last DDT'),
        'invoiced_current_year': fields.float(
            'Current invoiced', digits=(16, 2)),
        'invoiced_last_year': fields.float('Last invoiced', digits=(16, 2)),
        'order_current_year': fields.float('Current order', digits=(16, 2)),
        'order_last_year': fields.float('Last order', digits=(16, 2)),
        'invoice_trend': fields.function(
            _function_statistics_invoice, method=True, type='selection',
                selection=[
                    ('down','<'),
                    ('equal','='),
                    ('up','>'), ],
                        string='Invoice status', store=True, readonly=True,
                        multi='invoice_stat'),
        'invoice_trend_perc': fields.function(
            _function_statistics_invoice, method=True, type='float',
            digits=(16,2), string='Invoice diff. %', store=True, readonly=True,
            multi='invoice_stat'),
        'type_id': fields.many2one(
            'crm.tracking.campaign',
            # NOTE ex: 'crm.case.resource.type', 
            'Campaign'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
