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
import csv
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

class ResPartner(orm.Model):
    ''' Extra fields for manage pricelist
    '''
    _inherit = 'res.partner'

    _columns = {
        'ref_pricelist_id': fields.many2one(
            'product.pricelist.version', 'Ref. version pricelist'),
        }

class ProductPricelist(orm.Model):
    ''' Add scheduled operations
    '''
    _inherit = 'product.pricelist'

    # Utility:
    def create_pricelist(self, cr, uid, context=None):
        ''' Crate if not exist all [0:9] base pricelist - version
        '''
        version_pool = self.pool.get('product.pricelist.version')

        for pricelist in range(1, 10):
            mexal_id = str(pricelist)
            pl_ids = self.search(cr, uid, [
                ('mexal_id', '=', mexal_id,)], context=context)
            if pl_ids:
                pl_id = pl_ids[0]
            else:
                pl_id = self.create(cr, uid, {
                    'name': "Listino Mexal n. " + mexal_id,
                    #'currency_id': getCurrency(sock,dbname,uid,pwd,currency_ids[i]), # TODO
                    'type': 'sale',
                    'mexal_id': mexal_id,
                    })

            # Create base version (product.pricelist.version)
            version_ids = version_pool.search(cr, uid, [
                ('mexal_id', '=', mexal_id)], context=context)
            if not version_ids:
               version_pool.create(cr, uid, {
                   'name': "Versione base " + mexal_id,
                   'pricelist_id': pl_id,
                   'mexal_id': pricelist, # << extra fields
                   'import': True,        # <<
                   })
        return

    def get_partner_pricelist_ref(self, cr, uid, partner_code, context=None):
        ''' Return res_pricelist_if for partner passed
        '''
        partner_pool = self.pool.get('res.partner')
        partner_ids = partner_pool.search(cr, uid, [
            ('sql_customer_code', '=', partner_code)], context=context)
        if partner_ids:
            return partner_pool.browse(
                cr, uid, partner_ids, context=context)[
                    0].ref_pricelist_id.id or False
        return False

    def get_partner_pricelist(self, cr, uid, partner_code, context=None):
        ''' Search or Create a pricelist and a pricelist version
            return version ID
            Set also as default pricelist for partner
        '''
        # 0. Search for partner (associate pricelist after create)
        partner_pool = self.pool.get('res.partner')
        partner_ids = partner_pool.search(cr, uid, [
            ('sql_customer_code', '=', partner_code)], context=context)
        if partner_ids:
            partner_id = partner_ids[0]
        else: # Fast creation
            partner_id = partner_pool.create(cr, uid, {
                'name': "Partner %s" % partner_code,
                'sql_customer_code': partner_code,
                }, context=context)
        partner_proxy = partner_pool.browse(
            cr, uid, partner_id, context=context)

        # 1. case: version present (so pricelist and partner)
        version_pool = self.pool.get('product.pricelist.version')
        version_ids = version_pool.search(cr, uid, [
            ('mexal_id', '=', partner_code)], context=context)
        if version_ids:
            # update name:
            #version_pool.write(cr, uid, version_ids[0], {
            #    'name': "Versione base partner [%s]" % partner_proxy.name,
            #    }, context=context)
            return version_ids[0]

        # 2. case: version present (so pricelist and partner)
        pricelist_ids = self.search(cr, uid, [
            ('mexal_id', '=', partner_code)], context=context)
        # Check pricelist:
        if pricelist_ids:
            pricelist_id = pricelist_ids
            #self.write(cr, uid, pricelist_id, {
            #    'name': "Listino partner [%s]" % partner_proxy.name,
            #    }, context=context)
        else:
            # TODO: Current always create in EUR
            currency_ids = self.pool.get('res.currency').search(cr, uid, [
                ('name', '=', 'EUR')], context=context)
            pricelist_id = self.create(cr, uid, {
                'name': "Listino partner [%s]" % partner_proxy.name,
                'currency_id': currency_ids[0] if currency_ids else False,
                'type': 'sale',
                'import': True,
                'mexal_id': partner_code,
                }, context=context)

        # Update pricelist for partner:
        partner_pool.write(cr, uid, partner_id, {
            'property_product_pricelist': pricelist_id,
            }, context=context)

        # Create version:
        return version_pool.create(cr, uid, {
            'name': "Versione base partner [%s]" % partner_proxy.name,
            'pricelist_id': pricelist_id,
            'import': True,
            'mexal_id': partner_code,
            }, context=context)

    def schedule_csv_pricelist_import(self, cr, uid,
            input_file="~/ETL/artioerp.csv", delimiter=";", header_line=0,
            input_file_part="~/ETL/partioerp.csv", delimiter_part=";",
            header_line_part=0, verbose=100, context=None):
        ''' Import pricelist and setup particular price for partners
            (the partners are imported with SQL methods)

            This importation is generated from product csv file for standard
            pricelist, remember that there are also partner pricelist with
            particular price (not imported here)

            Note: pricelist yet present here (only item are unlink / create)
        '''

        # ---------------------------------------------------------------------
        #                            Common part
        # ---------------------------------------------------------------------
        csv_pool = self.pool.get('csv.base')
        item_pool = self.pool.get('product.pricelist.item')
        version_pool = self.pool.get('product.pricelist.version')
        product_pool = self.pool.get('product.product')

        # Erase all pricelist item (only) before import:
        item_ids = item_pool.search(cr, uid, [], context=context)
        item_pool.unlink(cr, uid, item_ids, context=context)

        # Crete if not exist 0:9 standard pricelist
        self.create_pricelist(cr, uid, context=context)
        # ---------------------------------------------------------------------
        #                  Load standard pricelist version (1-9):
        # ---------------------------------------------------------------------
        _logger.info("Start pricelist standard importation")
        versions = {} # dict of pricelist (mexal_id: odoo id)
        # Delete all version pricelist:
        # TODO get converter from previous function utility
        for item in range(1, 10): #1-9
            mexal_id = str(item)
            version_ids = version_pool.search(cr, uid, [
                ('mexal_id', '=', mexal_id)
                ], context=context)
            if version_ids:
               version_id = version_ids[0]
            else:
                # create pricelist and version return version id
                # TODO
                version_id = False

            versions[mexal_id] = version_id

        csv_file = open(os.path.expanduser(input_file), 'rb')
        counter = -header_line
        price_list = {} # dict for save product prices
        try:
            for line in csv.reader(csv_file, delimiter=delimiter):
                if counter < 0:  # jump n lines of header
                    counter += 1
                    continue

                if not len(line): # jump empty lines
                    continue
                if verbose and counter % verbose == 0:
                    _logger.info("Pricelist item created: %s" % counter)
                counter += 1
                default_code = csv_pool.decode_string(line[0])
                name = csv_pool.decode_string(line[1]).title()

                # NOTE: load only this pricelist (not all 10)
                price_list[1] = csv_pool.decode_float(line[6])
                price_list[4] = csv_pool.decode_float(line[7])
                price_list[5] = csv_pool.decode_float(line[8])
                price_list[6] = csv_pool.decode_float(line[9])

                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                if not product_ids:
                    _logger.error("Product not found %s" % default_code)
                    continue # jump (not created here)
                elif len(product_ids) > 1:
                    _logger.warning("Multiple product %s" % default_code)
                    continue # jump

                for pl in price_list:
                    if price_list[pl]:
                        item_pool.create(cr, uid, {
                        'price_version_id': versions[str(pl)],
                        'sequence': 10,
                        'name': default_code,
                        'base': 2, # 1 pl 2 cost
                        'min_quantity': 1,
                        'product_id': product_ids[0],
                        'price_discount': -1,
                        'price_surcharge': price_list[pl],
                        'price_round': 0.01,
                        }, context=context)
        except:
            _logger.error("Pricelist import %s" % (sys.exc_info(), ))
            return False

        # ---------------------------------------------------------------------
        #                Partner with particularity pricelist:
        # ---------------------------------------------------------------------
        _logger.info("Start pricelist partner particular importation")
        csv_file = open(os.path.expanduser(input_file_part), 'rb')
        counter = -header_line_part
        last_rule = {}
        try:
            for line in csv.reader(csv_file, delimiter=delimiter_part):
                if counter < 0:  # jump n lines of header
                    counter += 1
                    continue

                if not len(line): # jump empty lines
                    continue
                if verbose and counter % verbose == 0:
                    _logger.info("Partner PL item created: %s" % counter)
                counter += 1
                default_code = csv_pool.decode_string(line[0])
                partner_code = csv_pool.decode_string(line[1])
                price_list = csv_pool.decode_float(line[2])

                # Get product:
                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code),
                    ], context=context)
                if not product_ids:
                    _logger.error("Product not found %s" % default_code)
                    continue # jump (not created here)
                elif len(product_ids) > 1:
                    _logger.warning("Multiple product %s" % default_code)
                    continue # jump

                # Get pricelist version:
                if not partner_code:
                    _logger.error("Partner code not present!")
                    continue
                if partner_code not in versions:
                    # Save in versions dict converter
                    versions[partner_code] = self.get_partner_pricelist(
                        cr, uid, partner_code, context=context)
                    # Create version rule (last rule)
                    ref_pricelist_id = self.get_partner_pricelist_ref(
                        cr, uid, partner_code, context=context)
                    if ref_pricelist_id:
                        item_pool.create(cr, uid, {
                            'price_version_id': versions[partner_code],
                            'sequence': 9999,
                            'name': 'Listino di riferimento', # TODO number of pricelist
                            'base': -1,
                            'base_pricelist_id': ref_pricelist_id,
                            'min_quantity': 1,
                            'price_discount': 0.0,
                            'price_surcharge': 0.0,
                            'price_round': 0.01,
                            }, context=context)
                    else:
                        _logger.warning(
                            'Partner ref. pricelist not found %s' % (
                                partner_code, ))

                item_pool.create(cr, uid, {
                    'price_version_id': versions[partner_code],
                    'sequence': 10,
                    'name': default_code,
                    'base': 2, # 1 pl 2 cost
                    'min_quantity': 1,
                    'product_id': product_ids[0],
                    'price_discount': -1,
                    'price_surcharge': price_list,
                    'price_round': 0.01,
                    }, context=context)

        except:
            _logger.error("Pricelist import %s" % (sys.exc_info(), ))
            return False

        _logger.info("End pricelist import!")
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
