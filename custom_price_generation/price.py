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


class ProductCustomDuty(orm.Model):
    '''Anagrafic to calculate product custom duty depending of his category
       (using % of tax per supplier cost)
    '''
    _name = 'product.custom.duty'
    _description = 'Product custom duty'

    _columns = {
        'name': fields.char('Custom duty', size=100, required=True),
        'code': fields.char('Code', size=24),
        'tax_ids': fields.one2many(
            'product.custom.duty.tax', 'duty_id', '% Tax'),
        }

class ProductCustomDutyTax(orm.Model):
    '''Cost for country to import in Italy
    '''
    _name = 'product.custom.duty.tax'
    _description = 'Product custom duty tax'
    _rec_name = 'tax'

    _columns = {
        'tax': fields.float('% Tax', digits=(8, 3)),
        'country_id':fields.many2one('res.country', 'Country', required=True),
        'duty_id':fields.many2one('product.custom.duty', 'Duty code'),
        }

    _defaults = {
        'tax': lambda *a: 0.0,
    }

class BaseImageFolder(orm.Model):
    _name = 'base.image.folder'
    _description = 'Base image folder'

    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'addons': fields.boolean('Addons root path'),
        'root_path': fields.char('Foder extra path', size=128,
            help="Path extra default root folder, ex.: http://server/openerp"),
        'folder_path': fields.char('Foder extra path', size=128, required=True,
            help="Path extra default root folder, ex.: thumb/400/color"),
        'extension_image': fields.char('Extension', size=15, required=True,
            help="without dot, for ex.: jpg"),
        'default': fields.boolean('Default'),
        'width': fields.integer('Witdh in px.'),
        'height': fields.integer('Height in px.'),
        'empty_image': fields.char('Empty image', size=64, required=True,
            help="Complete name + ext. of empty image, ex.: 0.png"),
        }

    _defaults = {
        'default': lambda *x: False,
        }

class BaseProductExchange(orm.Model):
    '''Exchange USD to EUR
    '''
    _name = 'base.product.exchange'
    _description = 'Exchange product'

    def get_last_exchange(self, cr, uid, ids):
        '''Search last date exchange and return value
        '''
        try:
            exchange_ids = self.search(cr, uid, [], order="date DESC")
            exchange_read = self.read(cr, uid, exchange_ids[0], ['exchange',])
            if exchange_read:
               return round(exchange_read['exchange'], 2) or 0.0
            else:
               return 0.0
        except:
            return 0.0

    _columns = {
        'name': fields.char('Description', size=40, required=True),
        'exchange': fields.float('Exchange', digits=(16, 2)),
        'date': fields.date('Date of quotation'),
        }

    _defaults = {
        'exchange': lambda *x: 0.0,
        'date': lambda *a: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

class ProductProductHistoryCost(orm.Model):
    _name = 'product.product.history.cost'
    _order = 'date DESC'

    _columns = {
        'name':fields.char('Name of history', size=40, required=True,
            help="Calculated by importation wizard, es.: Year 2010"),
        'fob_cost': fields.float('FOB history cost USD', digits=(16, 2)),
        'fob_pricelist': fields.float('Pricelist EUR', digits=(16, 2)),
        'date': fields.date('Date of storicization'),
        'product_id': fields.many2one(
            'product.product', 'Product ref.', required=True),
        }

class PricelistPartnerinfoExtra(orm.Model):
    _inherit = 'pricelist.partnerinfo'

    def on_change_price_usd(self, cr, uid, ids, price_usd, context=None):
       '''Get USD price and translate in EUR value taken the last exchange value
       '''

       res = {'value': {'price': 0.0}}
       exchange = self.pool.get("base.product.exchange").get_last_exchange(
           cr, uid, ids, context=context)
       if exchange:
          res['value']['price']=round((price_usd / exchange), 2)

       return res

    _columns = {
        'price_usd': fields.float(
            'Unit Price USD', required=True,
            digits_compute=dp.get_precision('Purchase Price'))
        }

class ProductProductExtra(orm.Model):
    _inherit = 'product.product'

    # Fields function:
    def _get_fob_cost_default_selected(self, product):
        ''' In the product search default value for supplier setup as default
            (return the first)
        '''
        if not product.seller_ids:
            return 0.0
        for pricelist in product.seller_ids[0].pricelist_ids:
            if pricelist.is_active:
                return pricelist.price or 0.0
        if product.seller_ids[0].pricelist_ids:
            return product.seller_ids[0].pricelist_ids[0].price
        else:
            return 0.0

    def _get_fob_cost_default(
            self, cr, uid, ids, args, field_list, context=None):
        ''' Return default cost for first supplier
        '''
        product_proxy = self.browse(cr, uid, ids, context=context)
        res = {}
        for item in product_proxy:
            res[item.id] = {}
            exchange = self.pool.get(
                "base.product.exchange").get_last_exchange(
                    cr, uid, ids, context=context)
            price_eur = self._get_fob_cost_default_selected(item)
            if exchange:
               res[item.id]['fob_cost_supplier'] = price_eur * exchange
            else:
               res[item.id]['fob_cost_supplier']=0.0
            res[item.id]['fob_cost_supplier_eur'] = price_eur
        return res

    def _get_full_calculation(
            self, cr, uid, ids, args, field_list, context=None):
        ''' Return all calculation for eur conversion and pricelist
        '''
        if context is None:
           context = {}
        res = {}

        product_proxy = self.browse(cr, uid, ids, context=context)
        for item in product_proxy:
            res[item.id] = {}
            exchange = self.pool.get(
                "base.product.exchange").get_last_exchange(cr, uid, ids)

            calc_transport = item.transport_packaging or 0.0
            calc_cost = item.fob_cost_supplier or 0.0

            if exchange:
               res[item.id]['dazi_eur'] = item.dazi / exchange
               res[item.id]['fob_cost_total'] = round(calc_cost + item.dazi + (
                   calc_transport * exchange), 2)
               res[item.id]['fob_cost_total_eur'] = res[item.id][
                   'fob_cost_total'] / exchange
               res[item.id]['transport_packaging_usd'] = (
                   calc_transport * exchange)
               res[item.id]['fob_pricelist_compute'] = round(
                   (100 + item.margin) * res[item.id][
                       'fob_cost_total'] / 100, 2)
               res[item.id]['fob_pricelist_compute_eur'] = res[item.id][
                   'fob_pricelist_compute'] / exchange
            else:
               res[item.id]['dazi_eur'] = 0.0
        return res

    def _get_transport_cost_default(
            self, cr, uid, ids, args, field_list, context=None):
        ''' Return default cost first package
        '''
        package_proxy = self.browse(cr, uid, ids, context=context)
        res = {}
        for item in package_proxy:
            res[item.id] = item.packaging and item.packaging[
                0].transport_cost or 0.0
        return res

    # Button function:
    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def copy_price_calculated(self, cr, uid, ids, data, context=None):
        ''' Button function for copy calculated price in fields price
            TODO unificare con _get_fob_cost_default
        '''
        if context is None:
           context = {}

        res = {}
        product_proxy=self.browse(cr, uid, ids, context=context)
        exchange = self.pool.get("base.product.exchange").get_last_exchange(
            cr, uid, ids, context=context) or 0.0  # change EUR price only
        for item in product_proxy: # write EUR e USD price
            if context.get('start_from_cost',0):
               res['fob_cost_eur'] = item.seller_ids and \
                   item.seller_ids[0].pricelist_ids and \
                   item.seller_ids[0].pricelist_ids[0].price or 0.0
               res['fob_cost'] = item.seller_ids and \
                   item.seller_ids[0].pricelist_ids and \
                   item.seller_ids[0].pricelist_ids[0].price_usd or 0.0
            self.write(cr, uid, ids, res)
        return True

    def get_image(self, cr, uid, id):
        ''' Get folder (actually 200 px) and extension from folder obj.
            Calculated dinamically image from module image folder + extra path
            + ext.
            Return image
        '''
        img = ''
        folder_proxy = self.pool.get('base.image.folder')
        folder_ids = folder_proxy.search(cr, uid, [('width', '=', 200)])
        if folder_ids:
           folder_browse = folder_proxy.browse(cr, uid, folder_ids)[0]
           extension = "." + folder_browse.extension_image
           empty_image = folder_browse.empty_image
           if folder_browse.addons:
              image_path = tools.config[
                  'addons_path'] + '/base_fiam_pricelist/images/photo/' + \
                  folder_browse.folder_path + "/"
           else:
              image_path = folder_browse.root_path + '/' + \
                  folder_browse.folder_path + "/"

        else: # no folder image
           return img # empty!

        product_browse=self.browse(cr, uid, id)
        if product_browse.code:
            # codice originale
            try:
                (filename, header) = urllib.urlretrieve(
                    image_path + product_browse.code + extension)
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            # codice padre:

            # immagine vuota:
            if not img:
                try:
                    (filename, header) = urllib.urlretrieve(
                        image_path + empty_image)
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''
        return img

    def _get_image(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in ids:
            res[item] = self.get_image(cr, uid, item)
        return res

    _columns = {
        'preview': fields.function(_get_image, type="binary", method=True),
        'in_pricelist': fields.boolean('In Pricelist'),

        'error_import': fields.boolean('Import error'), # ERASE
        'dimension_text': fields.text('Dimensione (testuale)'), # ERASE
        'error_dimension': fields.boolean('Errore dimens.'), # ERASE

        # Cost calculation:
        'fob_cost_supplier': fields.function(
            _get_fob_cost_default, method=True, type='float',
            string='Cost from supplier', store=False, multi="supplier_cost"),
        'fob_cost_supplier_eur': fields.function(
            _get_fob_cost_default, method=True, type='float',
            string='Cost from supplier (EUR)', store=False,
            multi="supplier_cost"),
        'transport_packaging': fields.function(
            _get_transport_cost_default, method=True, type='float',
            string='Cost from packaging (EUR)', store=False),

        # Campi di input:
        'duty_id':fields.many2one('product.custom.duty', 'Custom duty'),
        'dazi': fields.float('Dazi (USD)', digits=(16, 2)),
        'margin': fields.float('% margin (calc)', digits=(5, 2)),
        'fixed_margin': fields.float('% margin (fixed)', digits=(5, 2)),

        # Campi calcolati:
        'dazi_eur': fields.function(_get_full_calculation, method=True,
            type='float', string='Dazi (EUR)', digits=(16, 2), store=False,
            multi="total_cost"),
        'transport_packaging_usd': fields.function(
            _get_full_calculation, method=True, type='float',
            string='Cost from packaging (USD)', store=False,
            multi="total_cost"),
        'fob_cost_total': fields.function(
            _get_full_calculation, method=True, type='float',
            string='FOB cost total (USD)', digits=(16, 2), store=False,
            multi="total_cost", help='FOB cost + transport + dazi'),
        'fob_cost_total_eur': fields.function(
            _get_full_calculation, method=True, type='float',
            string='FOB cost total (EUR)', digits=(16, 2), store=False,
            multi="total_cost"),
        'fob_pricelist_compute_eur': fields.function(
            _get_full_calculation, method=True, type='float',
            string='Pricelist compute (EUR)', digits=(16, 2), store=False,
            multi="total_cost"),
        'fob_pricelist_compute': fields.function(
            _get_full_calculation, method=True, type='float',
            string='Pricelist compute (UDS)', digits=(16, 2), store=False,
            multi="total_cost"),
        'manual_pricelist':fields.boolean('Manual pricelist', required=False,
            help="If manual pricelist user set up price and program compute "
                "margin, else margin is set up and price list is compute"),

        'fob_pricelist': fields.float('Pricelist (EUR)', digits=(16, 2)),

        'history_cost_ids': fields.one2many(
            'product.product.history.cost',
            'product_id', 'History cost'),
        }

    _defaults = {
        'manual_pricelist': lambda *x: False,
        'in_pricelist': lambda *x: False,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
