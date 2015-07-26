# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
##############################################################################
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



class SaleOrderExchange(orm.Model):
    ''' Currency list for to be used in quotation or in partner setup
    '''
    _name = 'sale.order.exchange'
    _description = 'Order exchange'

    _columns = {
        'name': fields.char(
            'Description', size=64, required=True, 
            help='Description of quotation (some currency may have more than '
                'one exchange value, historical, current or particular depend '
                'on customer'),
        'currency_id': fields.many2one('res.currency', 'Currency', 
            required=True),
        'date': fields.date('Date quotation'),
        'quotation': fields.float('Quotation', digits=(16, 2), 
            help='Quotation is for get Company currency from current selected',
            required=True),
    }

class SaleOrder(orm.Model):
    ''' Add extra field to sale.order
    '''
    _inherit = 'sale.order'

    # -----------------
    # Fields functions:
    # -----------------
    def _function_get_currency_value(self, cr, uid, ids, fields, args,
            context=None):
        ''' Calculate currency value
        '''
        res = {}
        for order in self.browse(cr, uid, ids, context = context):
            res[order.id] = {}
            change = order.sale_quotation_currency
            if order.currency_order and change:
                res[order.id][
                    'currency_amount_untaxed'] = order.amount_untaxed / change
                res[order.id][
                    'currency_amount_tax'] = order.amount_tax / change
                res[order.id][
                    'currency_amount_total'] =  order.amount_total / change
            else:
                res[order.id][
                    'currency_amount_untaxed'] = order.amount_untaxed
                res[order.id][
                    'currency_amount_tax'] = order.amount_tax
                res[order.id][
                    'currency_amount_total'] = order.amount_total
        return res    
            
    # -----------------
    # onchange functions:
    # -----------------
    def onchange_sale_currency(self, cr, uid, ids, sale_currency_id, 
            context=None):
        ''' Read currency when currency is changed
        '''
        res = {'value': {}}
        if sale_currency_id:        
            current_quotation = self.pool.get('sale.order.exchange').browse(
                cr, uid, sale_currency_id, context=context)
            res['value'][
                'sale_quotation_currency'] = current_quotation.quotation or 0.0
        else:
            res['value'][
                'sale_quotation_currency'] = 0.0
        return res
        
    # Override onchange function:
    def onchange_partner_id(self, cr, uid, ids, partner_id):
        ''' Add extra field onchange for new field to fill        
        '''
        res = super(sale_order_extra, self).onchange_partner_id(
            cr, uid, ids, partner_id)
        if not partner_id:
            res['value'].update({
                'currency_order': False,
                'sale_currency_id': False,
                'sale_quotation_currency': 0.0,
                })
            return res
        
        partner_proxy = self.pool.get('res.partner').browse(
            cr, uid, partner_id)
        # if currency is present setup order parameters:
        if partner_id and partner_proxy.sale_currency_id:
            res['value'].update({
                'currency_order': True,
                'sale_currency_id': partner_proxy.sale_currency_id.id,
                'sale_quotation_currency': 
                    partner_proxy.sale_currency_id.quotation,
                })
        else:
            res['value'].update({
                'currency_order': False,
                'sale_currency_id': False,
                'sale_quotation_currency': 0.0,
                })
        return res

    _columns = {
        'currency_order': fields.boolean('Currency order', 
            help='If the quotation / order need a currency transformation '
                '(usually depend on partner)'),
        'sale_currency_id': fields.many2one('sale.order.exchange', 'Currency'),
        'sale_quotation_currency': fields.float(
            'Quotation', digits=(16, 2), 
            help='Quotation applied in this offer (changeable)'),

        'currency_amount_untaxed': fields.function(
            _function_get_currency_value, method=True,
            type='float', digits=(16, 2), 
            string='Amount untaxed (currency)', store=False, 
            multi='conversion'),
        'currency_amount_tax': fields.function(
            _function_get_currency_value, method=True,
            type='float', digits=(16, 2), string='Amount tax (currency)', 
            store=False, multi='conversion'),
        'currency_amount_total': fields.function(
            _function_get_currency_value, method=True,
            type='float', digits=(16, 2), string='Amount total (currency)', 
            store=False, multi='conversion'),
        }

class SaleOrderLine(orm.Model):
    ''' Add extra field to sale.order
    '''
    _inherit = 'sale.order.line'

    # -----------------
    # Fields functions:
    # -----------------
    def _function_get_currency_value(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Calculate currency value
        '''
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {}
            change = line.order_id.sale_quotation_currency
            if line.order_id.currency_order and change:
                res[line.id][
                    'currency_price_unit'] = line.price_unit / change 
                res[line.id][
                    'currency_price_subtotal'] = line.price_subtotal / change
            else:
                res[line.id][
                    'currency_price_unit'] = line.price_unit
                res[line.id][
                    'currency_price_subtotal'] = line.price_subtotal
        return res
        
    _columns = {
        'currency_price_unit': fields.function(_function_get_currency_value, 
            method=True, type='float', digits=(16, 2), 
            string='Price (currency)', store=False, multi='conversion'),
        'currency_price_subtotal': fields.function(
            _function_get_currency_value, method=True,
            type='float', digits=(16, 2), string='Subtotal (currency)', 
            store=False, multi='conversion'),
        }

class ResPartner(osv.osv):
    ''' Add default currency for partner
    '''
    _inherit = 'res.partner'

    _columns = {
        'sale_currency_id': fields.many2one('sale.order.exchange', 'Currency'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
