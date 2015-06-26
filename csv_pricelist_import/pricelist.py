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
            'product.pricelist', 'Ref. pricelist'),
        }

class ProductPricelistItem(orm.Model):
    ''' Extra fields
    '''
    _inherit = 'product.pricelist.item'

    _columns = {
        'default_pricelist': fields.boolean('Default pricelist rule'),
        }

class ProductPricelist(orm.Model):
    ''' Add scheduled operations
    '''
    _inherit = 'product.pricelist'

    # Utility:
    def create_default_pricelist(self, cr, uid, versions, context=None):
        ''' Crate if not exist all [0:9] base pricelist - version
            Update versions converter
        '''
        version_pool = self.pool.get('product.pricelist.version')

        # Create pricelist 1-9
        for pricelist in range(1, 10):
            mexal_id = str(pricelist)
            pl_ids = self.search(cr, uid, [
                ('mexal_id', '=', mexal_id,)], context=context)
            if pl_ids:
                pl_id = pl_ids[0]
            else:
                pl_id = self.create(cr, uid, {
                    'name': "Listino Mexal n. " + mexal_id,
                    #'currency_id': 
                    'type': 'sale',
                    'mexal_id': mexal_id,
                    })

            # Create version (updare converter)
            version_ids = version_pool.search(cr, uid, [
                ('mexal_id', '=', mexal_id)], context=context)
            if version_ids:
               versions[mexal_id] = version_ids[0]
            else:    
               versions[mexal_id] = version_pool.create(cr, uid, {
                   'name': "Versione base " + mexal_id,
                   'pricelist_id': pl_id,
                   'mexal_id': pricelist,
                   })
        return

    def get_partner_pricelist(self, cr, uid, partner_code, context=None):
        ''' Search or Create a pricelist and a pricelist version
            return version ID
            Set also as default pricelist for partner
            Set default rule in version pricelist (always update)
        '''
        # --------
        # Utility:
        # --------
        def update_reference_pl(self, cr, uid, pricelist_id, ref, context=None):
            ''' Update last rule of pricelist with default partner
            '''
            if not ref:
                return False

            item_pool = self.pool.get('product.pricelist.item')
            item_ids = item_pool.search(cr, uid, [
                ('price_version_id', '=', pricelist_id),                
                ('default_pricelist', '=', True),
                ], context=context)
            data = {
                'price_version_id': pricelist_id,
                'sequence': 9999, # max number for automated rules
                'name': 'Listino di riferimento', # TODO number of pricelist
                'base': -1,
                'base_pricelist_id': ref,
                'min_quantity': 1,
                'price_discount': 0.0,
                'price_surcharge': 0.0,
                'price_round': 0.01,
                'default_pricelist': True,
                }    
            if item_ids:
                item_pool.write(cr, uid, item_ids, data, context=context)
            else:
                item_pool.create(cr, uid, data, context=context)
            return True
            
        # ------------------
        # Search for partner
        # ------------------
        # Associate pricelist after create
        partner_pool = self.pool.get('res.partner')
        partner_ids = partner_pool.search(cr, uid, [
            ('sql_customer_code', '=', partner_code)], context=context)
        if partner_ids:
            partner_id = partner_ids[0]
        else: # Fast creation of partner
            partner_id = partner_pool.create(cr, uid, {
                'name': "Partner %s (from pricelist)" % partner_code,
                'sql_customer_code': partner_code,
                }, context=context)
        partner_proxy = partner_pool.browse(
            cr, uid, partner_id, context=context)

        # 1. case: version present (so pricelist and partner)
        version_pool = self.pool.get('product.pricelist.version')
        version_ids = version_pool.search(cr, uid, [
            ('mexal_id', '=', partner_code)], context=context)
        if version_ids: # TODO update?            
            update_reference_pl( # Update last rule:
                self, cr, uid, 
                version_ids[0], 
                partner_proxy.ref_pricelist_id.id, 
                context=context)
            return version_ids[0]

        # 2. case: version present (so pricelist and partner)
        pricelist_ids = self.search(cr, uid, [
            ('mexal_id', '=', partner_code)], context=context)

        # Check pricelist:
        if pricelist_ids:
            pricelist_id = pricelist_ids[0]
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
        version_id = version_pool.create(cr, uid, {
            'name': "Versione base partner [%s]" % partner_proxy.name,
            'pricelist_id': pricelist_id, 
            'mexal_id': partner_code,
            }, context=context)

        # Update last rule
        update_reference_pl(
            self, cr, uid, 
            version_id, 
            partner_proxy.ref_version_id.id, 
            context=context)
        return

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
        # Pool used:
        # self is product.pricelist
        version_pool = self.pool.get('product.pricelist.version')
        item_pool = self.pool.get('product.pricelist.item')
        product_pool = self.pool.get('product.product')
        csv_pool = self.pool.get('csv.base')

        # Erase all pricelist item (only) before import:
        item_ids = item_pool.search(cr, uid, [], context=context)
        item_pool.unlink(cr, uid, item_ids, context=context)

        # ---------------------------------------------------------------------
        #                  Load standard pricelist version (1-9):
        # ---------------------------------------------------------------------
        _logger.info("Start pricelist standard importation: %s" % (
            input_file, ))
        versions = {} # dict of pricelist (mexal_id: odoo id)
        self.create_default_pricelist(cr, uid, versions, context=context) # pl + vers.

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
                if verbose and counter and counter % verbose == 0:
                    _logger.info("# Pricelist item created: %s" % counter)
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

                # Update item in all standard version:
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
            _logger.error("Stopped pricelist import %s" % (sys.exc_info(), ))
            return False

        # ---------------------------------------------------------------------
        #                Partner with particularity pricelist:
        # ---------------------------------------------------------------------
        _logger.info("Start pricelist partner item importation: %s" % (
            input_file_part, ))
        csv_file = open(os.path.expanduser(input_file_part), 'rb')
        counter = -header_line_part
        try:
            for line in csv.reader(csv_file, delimiter=delimiter_part):
                if counter < 0:  # jump n lines of header
                    counter += 1
                    continue

                if not len(line): # jump empty lines
                    continue
                if verbose and counter and counter % verbose == 0:
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
                    continue # jump (TODO created here?)
                elif len(product_ids) > 1:
                    _logger.warning("Multiple product %s" % default_code)
                    continue # jump

                # Get pricelist version:
                if not partner_code:
                    _logger.error("Partner code not present!") # TODO create?                    
                    continue
                if partner_code not in versions: # Save in versions converter
                    versions[partner_code] = self.get_partner_pricelist(
                        cr, uid, partner_code, context=context)

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
