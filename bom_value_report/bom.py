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


class MrpBomExtraFields(orm.Model):
    _inherit ='mrp.bom'
    _order = 'name,code'

    def get_bom_element_price(self, cr, uid, bom_id, context=None):
        ''' Procedura ricorsiva per calcolo prezzo distinta base
            return total of sub bom_lines (recursive)
        '''
        browse_bom_id = self.browse(cr, uid, bom_id, context=context)
        if browse_bom_id:
           if browse_bom_id.bom_lines:
              total = 0.0
              for item_bom_id in browse_bom_id.bom_lines:
                  total += self.get_bom_element_price(
                      cr, uid, item_bom_id.id, context=context) or 0.0
              return total
           else:
              return browse_bom_id.actual_total or 0.0 # recurse exit
        else:
           return 0.0

    def _get_fields_component(
            self, cr, uid, ids, args, field_list, context=None):
        ''' 1. Calcola il totale dei componenti presenti nella distinta base
            2. Verifica che il componente non sia stato indicato come obsoleto
            oppure controlla che la quotazione non sia più vecchia del 01/01
            di due anni prima
            3. Calcola il prezzo del componente (data minore o primo che trova)
               NB: dovrebbe esserci solo un fornitore
        '''
        res = {}
        riferimento = str(int(datetime.strftime(
            datetime.now(),"%Y"))-2) + "-01-01"
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {}
            res[item.id]['tot_component'] = len(item.bom_lines)
            res[item.id]['old_cost'] = False
            res[item.id]['actual_price'] = 0.0
            res[item.id]['first_supplier'] = False
            price = 0.0
            date_max = False
            first_supplier = 0
            for seller in item.product_id.seller_ids:
                # loop all quotation:
                for pricelist in seller.pricelist_ids:
                    if pricelist.is_active:
                        if pricelist.date_quotation:
                           # component price:
                           if date_max < pricelist.date_quotation:
                               date_max = pricelist.date_quotation
                               price = pricelist.price
                               first_supplier = (
                                   seller.name and seller.name.id) or False
                        else: # data di quotazione vuota, prezzo presente
                           if not date_max: # if not data max take price
                               price = pricelist.price
                               first_supplier = (
                                   seller.name and seller.name.id) or False

            # Set value after loop for customers
            if date_max <= riferimento:  # only one
               res[item.id]['old_cost'] = True
            else:
               res[item.id]['old_cost'] = True

            res[item.id]['actual_price'] = price or 0.0
            res[item.id]['actual_total'] = (price or 0.0) * (
                item.product_qty or 0.0)
            res[item.id]['first_supplier'] = first_supplier
        return res

    _columns = {
        'product_qty': fields.float('Product Qty', digits=(8,5),
            required=True),
        'obsolete': fields.boolean('Obsolete',
            help='Is better do not use this component!'),
        'note': fields.text('Note'),

        # Fields function:
        'tot_component': fields.function(
            _get_fields_component, method=True, type='integer',
            string="Tot comp", store= True, multi=True),
        'old_cost': fields.function(
            _get_fields_component, method=True, type='boolean',
            string="Old price", store=True, multi=True),
        'actual_price': fields.function(
            _get_fields_component, method=True, type='float',
            string="Price", digits=(8,5), store=False, multi = True,),
        'actual_total': fields.function(
            _get_fields_component, method=True, type='float',
            string="Subtotal", digits=(8,5), store=False, multi=True),
        'first_supplier': fields.function(
            _get_fields_component, method=True, type='many2one',
            relation="res.partner", string="Primo forn.", store=False,
            multi=True),
       }

    _defaults = {
        'obsolete': lambda *a: False,
        }

class PricelistPartnerinfoExtraFields(orm.Model):
    _inherit ='pricelist.partnerinfo'

    def _has_bom_funct(self, cr, uid, ids, args, field_list, context=None):
        res = dict.fromkeys(ids, False)
        product_list = []
        product_ids_convert = {}

        # load product
        for pricelist in self.browse(cr, uid, ids):
            if (pricelist.product_id) and (
                    pricelist.product_id.id not in product_list):
                product_list.append(str(pricelist.product_id.id))
                product_ids_convert[pricelist.product_id.id] = pricelist.id

        query = """
            SELECT distinct product_id
            FROM mrp_bom
            WHERE product_id in (%s);""" % (",".join(product_list))
        cr.execute(query)

        for item_id in cr.fetchall():
            res[product_ids_convert[item_id[0]]] = True # True all finded
        return res

    _columns = {
        'is_active': fields.boolean("Active", required=False,
            help="Check last price line (only this for every Q)"),
        'date_quotation': fields.date('Date quotation'),
        'price': fields.float('Unit Price', required=True, digits=(8,5),
            help="This price will be considered as a price for the supplier "
                "UoM if any or the default Unit of Measure of the product "
                "otherwise"),
        'supplier_id': fields.related(
            'suppinfo_id','name', type='many2one', relation='res.partner',
            string='Supplier'),
        'product_id': fields.related(
            'suppinfo_id', 'product_id', type='many2one',
            relation='product.template', string='Desc. prod./comp.',
            store=True),
        'product_supp_name': fields.related(
            'suppinfo_id','product_name', type='char', size=128,
            string="Supplier description"),
        'product_supp_code': fields.related(
            'suppinfo_id','product_code', type='char', size=64,
            string="Supplier code"),
        'product_name': fields.related(
            'product_id', 'name', type='char', string='Desc. prod./comp.'),
        'uom_id': fields.related('product_id','uom_id', type='many2one',
            relation='product.uom', string='UM'),
        'has_bom': fields.function(_has_bom_funct, method=True, type='boolean',
            string="Is BOM", store=False),
    }

    _defaults = {
        'is_active': lambda *a: True,
    }

class ProductProductExtraFields(orm.Model):
    _inherit ='product.product'

    def _get_bom_ids_len(self, cr, uid, ids, args, field_list, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id]=len(product.bom_ids)
        return res

    def _get_first_supplier_funct(
            self, cr, uid, ids, args, field_list, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {}
            if product.seller_ids:
               res[product.id]['first_code'] = product.seller_ids[
                   0].product_code
               res[product.id]['first_supplier'] = product.seller_ids[
                   0].name.id
            else:
               res[product.id]['first_code'] = ''
               res[product.id]['first_supplier'] = False
        return res

    def _get_best_cost_funct(self, cr, uid, ids, args, field_list, context=None):
        res = dict.fromkeys(ids, 0)
        for product in self.browse(cr, uid, ids, context=context):
            price = []
            for seller in product.seller_ids:
                for pricelist in seller.pricelist_ids:
                    if pricelist.is_active:
                       price.append(pricelist.price)
            if price:
               res[product.id] = min(price)
            else:
               res[product.id] = 0.0
        return res

    _columns = {
        'best_cost': fields.function(
            _get_best_cost_funct, method=True, type='float',
            string='Best cost', store=False),
        'first_supplier': fields.function(
            _get_first_supplier_funct, method=True, type='many2one',
            relation='res.partner', string='Primo fornitore', store=True,
            multi='First delivery'),
        'first_code': fields.function(
            _get_first_supplier_funct, method=True, type='char', size=64,
            string='First code', store=True, multi='First delivery',),
        'bom_len': fields.function(_get_bom_ids_len, method=True,
            type='integer', string='Tot. comp.', store=True),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
