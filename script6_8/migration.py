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
import xmlrpclib
import erppeek
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)

class SyncroXMLRPC(orm.Model):
    ''' Function for migration (and setup parameters for XMLRPC)
        So no file .cfg to setup
    '''
    _name = 'syncro.xmlrpc'

    _converter = {}

    def load_converter(self, cr, uid, converter, obj,
            field_id='migration_old_id', context=None):
        ''' Load coverter if not present
        '''
        item_pool = self.pool.get(obj)
        item_ids = item_pool.search(cr, uid, [
            (field_id, '!=', False),
            (field_id, '!=', 0),
            ], context=None)
        for item in item_pool.browse(
                cr, uid, item_ids, context=context):
            converter[item.__getattribute__(field_id)] = item.id
        return

    # -------------------------------------------------------------------------
    # Syncro / Migration procedures:
    # -------------------------------------------------------------------------
    def migrate_database(self, cr, uid, wiz_proxy, context=None):
        ''' Module for syncro partner from one DB to another
            This method implement some utility function
            and all the selectable function that could be lauched from wizard
        '''

        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def get_product_category(self, cr, uid, name, context=context):
            ''' Search category or create if not present
            '''
            try:
                category_pool = self.pool.get('product.category')
                category_ids = category_pool.search(cr, uid, [
                    ('name', '=', name)], context=context)
                if category_ids:
                    return category_ids[0]
                return category_pool.create(cr, uid, {
                    'name': name,
                    #'parent_id': self.categ_all, # TODO setup parent category
                    }, context=context)
            except:
               print "#ERR Create employee category:", sys.exc_info()
               return False

        # ---------------------------------------------------------------------
        #        Common part: connection to old database using ERPEEK
        # ---------------------------------------------------------------------
        # First record only
        item_ids = self.search(cr, uid, [], context=context)
        if not item_ids:
           return False

        openerp = self.browse(cr, uid, item_ids[0], context=context)

        # ERPPEEK CLIENT:
        erp = erppeek.Client(
            'http://%s:%s' % (openerp.hostname, openerp.port),
            db=openerp.name,
            user=openerp.username,
            password=openerp.password,
            )
        
        # Add extra socket for XMLRPC for problem in reading of erpeek
        # XMLRPC connection for autentication (UID) and proxy 
        sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (
            openerp.hostname, 
            openerp.port), allow_none=True)            
        user_id = sock.login(openerp.name, openerp.username, openerp.password)
        sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (
            openerp.hostname,
            openerp.port), allow_none=True)
        
        from_date = wiz_proxy.from_date or False
        to_date = wiz_proxy.to_date or False

        # ---------------------------------------------------------------------
        #          SIMPLE OBJECT (LOAD OR CREATE)  << ALWAYS RUN
        # ---------------------------------------------------------------------
        
        # -----------------
        # product.uom.categ
        # -----------------
        #Load and create extra
        obj = 'product.uom.categ'
        _logger.info("Start %s" % obj)
        obj_pool = self.pool.get(obj)
        self._converter[obj] = {}    
        obj_ids = obj_pool.search(cr, uid, []) #context=context)
        # Read currenct:
        for item in obj_pool.browse(cr, uid, obj_ids): #context=context):
            self._converter[obj][item.name] = item.id
            
        # Create extra:    
        for name in ('Area', 'Capacity', 'Electric Power', 'Volume'):
            if name not in self._converter[obj]:
                self._converter[obj][
                    name] = obj_pool.create(cr, uid, {
                        'name': name,
                        }, context=context)

        # -----------
        # product.uom
        # -----------
        #Load and create extra UOM
        obj = 'product.uom'
        _logger.info("Start %s" % obj)
        obj_pool = self.pool.get(obj)        
        self._converter[obj] = {}    
        obj_ids = obj_pool.search(cr, uid, []) #context=context) # for lang
        for item in obj_pool.browse(cr, uid, obj_ids): #context=context):
            self._converter[obj][item.name] = item.id
            
        for record in (
                {
                    'name': 'M2', 
                    'factor_inv': 1.0, 
                    'rounding': 0.01, 
                    'uom_type': 'reference', 
                    'factor': 1.0, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Area'],
                    },
                {
                    'name': 'LT', 
                    'factor_inv': 1.0, 
                    'rounding': 0.01, 
                    'uom_type': 'reference', 
                    'factor': 1.0, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Capacity'],
                    },
                {
                    'name': 'PK', 
                    'factor_inv': 1000.0, 
                    'rounding': 1.0, 
                    'uom_type': 'bigger', 
                    'factor': 0.001, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Unit'],
                    },
                {
                    'name': 'P2', # Paia
                    'factor_inv': 2.0, 
                    'rounding': 1.0, 
                    'uom_type': 'bigger', 
                    'factor': 0.5, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Unit'],
                    },
                {
                    'name': 'P10', # Decine
                    'factor_inv': 10.0, 
                    'rounding': 1.0, 
                    'uom_type': 'bigger', 
                    'factor': 0.1, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Unit'],
                    },
                {
                    'name': 'KW', 
                    'factor_inv': 1.0, 
                    'rounding': 0.01, 
                    'uom_type': 'reference', 
                    'factor': 1.0, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Electric Power'],
                    },                                        
                {
                    'name': 'M3', 
                    'factor_inv': 1.0, 
                    'rounding': 0.01, 
                    'uom_type': 'reference', 
                    'factor': 1.0, 
                    'active': True, 
                    'category_id': self._converter['product.uom.categ'][
                        'Volume'],
                    }):
            if record['name'] not in self._converter[obj]:
                self._converter[obj][
                    record['name']] = obj_pool.create(
                        cr, uid, record, context=context)
        
        # ------------
        # res.currency
        # ------------
        obj = 'res.currency'
        _logger.info("Start %s" % obj)
        obj_pool = self.pool.get(obj)
        self._converter[obj] = {}
        obj_ids = obj_pool.search(cr, uid, [], context=context)
        for item in obj_pool.browse(
                cr, uid, obj_ids, context=context):
            self._converter[obj][item.name] = item.id

        # -----------------------
        # Supplier price history:
        # -----------------------
        supplier_pool = self.pool.get('product.supplierinfo')
        pl_pool = self.pool.get('pricelist.partnerinfo')
        history_pool = self.pool.get('pricelist.partnerinfo.history')
        auto_set_active = []
        delete_price = []
        if wiz_proxy.history:
            _logger.info("Start history supplier price")
            supplier_ids = supplier_pool.search(cr, uid, [], context=context)
            _logger.info('Record to update: %s' % len(supplier_ids))
            i = 0
            for supplier in supplier_pool.browse(cr, uid, supplier_ids, 
                    context=context):
                i += 1
                
                # ------------
                # Find active:
                # ------------
                if len(supplier.pricelist_ids) == 1:
                    # All forced (not test)
                    auto_set_active.append(supplier.pricelist_ids[0].id)
                    continue # next record!    

                active_id = False                
                for price in supplier.pricelist_ids:
                    if price.is_active:
                        active_id = price.id
                        break
                        
                if not active_id:
                    _logger.error('No active price in product: %s' % (
                        supplier.product_tmpl_id.name))
                    continue           
                # --------
                # History: 
                # --------
                for price in supplier.pricelist_ids:
                    if not price.is_active:
                        history_data = {
                            'pricelist_id': active_id,
                            'price': price.price,
                            'date_quotation': price.date_quotation,
                            'min_quantity': price.min_quantity,
                            }
                        history_pool.create(
                            cr, uid, history_data, context=context)     
                   
                        # TODO not for now:        
                        delete_price.append(price.id)
                        
                _logger.info('%s History record #: %s' % (
                    i, supplier.product_tmpl_id.name))
                    
            # Set only one record to active:            
            pl_pool.write(cr, uid, auto_set_active, {
                'is_active': True}, context=context)
            
            # Delete all historied price:    
            pl_pool.unlink(
                cr, uid, delete_price, context=context)
        
        # ------------------
        # Pricelist history:
        # ------------------
        if wiz_proxy.history:
            _logger.info("Start update history supplier price")
            history_pool = self.pool.get('pricelist.partnerinfo')
            history_ids = history_pool.search(cr, uid, [], context=context)
            _logger.info('Record to update: %s' % len(history_ids))
            i = 0
            for item_id in history_ids:
                i += 1
                data = history_pool._get_parent_information(
                    cr, uid, item_id, False, False, context=context)[item_id]                    
                #data['id'] = item_id
                history_pool.write(cr, uid, item_id, data, context=context)
                _logger.info('%s. Update: %s' % (i, data))
        
        # ------------
        # product.ul
        # ------------
        if wiz_proxy.package:
            _logger.info("Start %s" % obj)
            obj = 'product.ul'
            obj_pool = self.pool.get(obj)
            self._converter[obj] = {}
            
            erp_pool = erp.ProductUl
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                ul_ids = obj_pool.search(cr, uid, [
                    ('name', '=', item.name)], context=context)
                if not ul_ids:
                    item_id = obj_pool.create(cr, uid, {
                        'name': item.name,
                        'type': item.type,
                        }, context=context) 
                else:
                    item_id = ul_ids[0]
                self._converter[obj][item.name] = item_id
 
        # TODO removed for pricelist supplier import:
        '''
        # ----------------------
        # product.pricelist.type
        # ----------------------
        """obj = 'product.pricelist.type'
        obj_pool = self.pool.get(obj)
        self._converter[obj] = {}
        obj_ids = obj_pool.search(cr, uid, [], context=context)
        for item in obj_pool.browse(
                cr, uid, obj_ids, context=context):
            self._converter[obj][item.name] = item.id"""

        # --------------------------------------
        # product.pricelist (first 10 pricelist)
        # --------------------------------------
        obj = 'product.pricelist'
        _logger.info("Start %s" % obj)
        obj_pool = self.pool.get(obj)
        self._converter[obj] = {}
        obj_ids = obj_pool.search(cr, uid, [
            ('import', '=', True)], context=context)

        # Load current
        for item in obj_pool.browse(
                cr, uid, obj_ids, context=context):
            self._converter[obj][item.mexal_id] = item.id
        
        # Create first 9 pricelist >> save in converter[number] = id 
        for item in range(1, 10):
            name = "Listino Mexal n. %s" % item
            if item not in self._converter[obj]:
                self._converter[obj][item] = obj_pool.create(cr, uid, {
                    'name': name,
                    'currency_id': self._converter['res.currency']['EUR'],
                    'type': 'sale',
                    'import': True,
                    'mexal_id': item,                    
                    }, context=context)

        # ----------------------------------------------
        # product.pricelist.version (first 10 pricelist)
        # ----------------------------------------------
        obj = 'product.pricelist.version'
        _logger.info("Start %s" % obj)
        obj_pool = self.pool.get(obj)
        self._converter[obj] = {}
        obj_ids = obj_pool.search(cr, uid, [
            ('import', '=', True)], context=context)

        # Load current
        for item in obj_pool.browse(
                cr, uid, obj_ids, context=context):
            self._converter[obj][item.mexal_id] = item.id
        
        # Create first 9 version >> save in converter[number] = id 
        for item in range(1, 10):
            name = "Versione base n. %s" % item
            if item not in self._converter[obj]:
                self._converter[obj][item] = obj_pool.create(cr, uid, {
                    'name': name,
                    'pricelist_id': self._converter['product.pricelist'][item], 
                    'import': True,
                    'mexal_id': item,                    
                    }, context=context)            
        ''' # TODO to here!
        # ---------------------------------------------------------------------
        # res.users
        # ---------------------------------------------------------------------
        obj = 'res.users'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # for use same name
        if wiz_proxy.user:
            erp_pool = erp.ResUsers
            item_pool = self.pool.get(obj)
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try:
                    # Create record to insert / update
                    data = {
                        'name': item.name,
                        'login': item.login,
                        'active': item.active,
                        'signature': item.signature,
                        'migration_old_id': item.id,
                        }
                    if 'admin' != item.login:
                        data['password'] = item.password

                    new_ids = item_pool.search(cr, uid, [
                        ('login', '=', item.login)],  # search login
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", obj, "update:", item.name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", item.name

                    converter[item.id] = item_id
                except:
                    print "#ERR", obj, "jumped:", item.name
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

        # ---------------------------------------------------------------------
        # account.tax
        # ---------------------------------------------------------------------
        ''' # TODO remove for pricelist
        tax_22v = False
        tax_22a = False
        if wiz_proxy.sale_line or wiz_proxy.purchase_line: # TODO or if needed in other tables 
            obj = 'account.tax'
            _logger.info("Start %s" % obj)
            tax_invert = {
                '22a': '22v',
                '22b': '22a',
                '00b': '00v',
                '20b': '20a',
                '10b': '10a',
                '12b': '12a',
                '4b': '4a',
                '21b': '21a',
                }
            self._converter[obj] = {}
            converter = self._converter[obj]
            item_pool = self.pool.get(obj)
            erp_pool = erp.AccountTax 
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try:
                    # Create record to insert/update
                    description = item.description
                    if description in tax_invert:
                        description = tax_invert[description]
                    new_ids = item_pool.search(cr, uid, [
                        ('description', '=', description)], context=context)
                    if new_ids: # Modify
                        converter[item.id] = new_ids[0]
                        if description == '22v':
                            tax_22v = new_ids[0]
                        if description == '22a':
                            tax_22a = new_ids[0]
                    else: # Create
                        #item_id = item_pool.create(cr, uid, data,
                        #    context=context)
                        print "#INFO", obj, "Error tax to create:", description

                except:
                    print "#ERR", obj, "jumped:", description
                    continue

        # ---------------------------------------------------------------------
        # crm.tracking.campaign
        # ---------------------------------------------------------------------
        obj = 'crm.tracking.campaign'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # for use same name
        if wiz_proxy.campaign: # TODO
            item_pool = self.pool.get(obj)
            erp_pool = erp.CrmCaseResourceType #TODO CrmCaseCateg
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try:
                    # Create record to insert/update
                    name = item.name
                    data = {'name': name}
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", obj, "jumped:", name
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

        # ---------------------------------------------------------------------
        # res.partner.category
        # ---------------------------------------------------------------------
        obj = 'res.partner.category' # Tags partner
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # for use same name
        if wiz_proxy.category: # TODO
            item_pool = self.pool.get(obj)
            erp_pool = erp.CrmCaseCateg
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try:
                    # Create record to insert/update
                    name = item.name
                    data = {
                        'name': name,
                        'migration_old_id': item.id,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", obj, "jumped:", name
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

        # ---------------------------------------------------------------------
        # product.category
        # ---------------------------------------------------------------------
        obj = 'product.category'
        self._converter[obj] = {}
        _logger.info("Start %s" % obj)
        converter = self._converter[obj] # for use same name
        if wiz_proxy.category:
            item_pool = self.pool.get(obj)
            erp_pool = erp.ProductCategory
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try:
                    # Create record to insert/update
                    name = item.name
                    data = {
                        'name': name,
                        'migration_old_id': item.id,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context) # Search name
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", obj, "jumped:", name
                    continue
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)                
        # 2nd loop: Category set parent_id:
        if wiz_proxy.category:
            item_ids = erp_pool.search([('parent_id', '!=', False)])
            for item in erp_pool.browse(item_ids):
                try:
                    parent_id = converter.get(
                        item.parent_id.id, False)
                    data = {'parent_id': parent_id, }
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_pool.write(cr, uid, new_ids[0], data,
                            context=context)
                        print "#INFO", obj, "update:", item.name
                except:
                    print "#ERR", obj, "jumped:", item.name
                    continue

        # before: web.category, web.color, product.custom.duty, 
        # web.line, web.tipology, 
        # TODO uom!!!
        ''' # TODO
        
        # ---------------------------------------------------------------------
        # product.product
        # ---------------------------------------------------------------------
        obj = 'product.product' # template??
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.product:
            item_pool = self.pool.get(obj)
            erp_pool = erp.ProductProduct
            erp_tmpl_pool = erp.ProductTemplate
            item_ids = erp_pool.search([])
            i = 0
            for item in erp_pool.browse(item_ids):
                try:
                    # PARENT analytic account:
                    i += 1
                    name = item.name.split("] ")[-1]
                    categ_id = self._converter['product.category'].get(
                        item.categ_id.id, False)

                    # Create record to insert / update
                    """
                    'amazon_mig_brand', 'amazon_mig_category1_id', 
                    'amazon_mig_category2_id', 'amazon_mig_color', 
                    'amazon_mig_country_id', 
                    'amazon_mig_description', 'amazon_mig_destination_code', 
                    'amazon_mig_dimension_um', 'amazon_mig_discount_end', 
                    'amazon_mig_discount_price', 'amazon_mig_discount_start', 
                    'amazon_mig_function', 'amazon_mig_gift', 
                    'amazon_mig_height', 
                    'amazon_mig_image', 'amazon_mig_image_publish', 
                    'amazon_mig_inventory', 'amazon_mig_is_image', 
                    'amazon_mig_keywords', 'amazon_mig_length', 
                    'amazon_mig_manage_days', 'amazon_mig_manufacturer', 
                    'amazon_mig_material', 'amazon_mig_migration', 
                    'amazon_mig_min_level', 'amazon_mig_out', 
                    'amazon_mig_price', 'amazon_mig_publish', 
                    'amazon_mig_q_x_pack', 'amazon_mig_sale_end', 
                    'amazon_mig_sale_start', 
                    'amazon_mig_security_level', 'amazon_mig_title', 
                    'amazon_mig_volume', 'amazon_mig_volume_um', 
                    'amazon_mig_warranty', 'amazon_mig_weight', 
                    'amazon_mig_weight_um', 'amazon_mig_width', 
                    'bom_len', 'company_id', 'copy', 'cost_method', 
                    'k2_alias', 'k2_all_product', 'k2_category_ids', 
                    'k2_extra_field_search', 'k2_extra_fields', 'k2_fulltext', 
                    'k2_gallery', 'k2_gallery_id', 'k2_image_caption', 
                    'k2_image_format', 'k2_introtext', 
                    'k2_mod_custom_ids', 'k2_ordering', 'k2_params', 
                    'k2_subtipology_ids', 
                    'loc_case', 'loc_rack', 'loc_row', 'mes_type', 
                    'packaging',
                    'procure_method', 'produce_delay', 'product_manager', 
                    'property_account_expense', 'property_account_income', 
                    'property_stock_account_input', 
                    'property_stock_account_output', 
                    'property_stock_inventory', 
                    'property_stock_procurement', 'property_stock_production', 
                    'purchase_ok', 'read', 'refresh', 'rental', 'sale_delay', 
                    'sale_ok', 'seller_delay', 'seller_id', 'seller_qty', 
                    'standard_price', 'state', 'supplier_taxes_id', 
                    'supply_method', 'taxes_id', 'unlink', 'uom_id', 
                    'uom_po_id', 
                    'uos_coeff', 'uos_id', 'volume', 'warranty', 'weight', 
                    'width', 'write'
                    """
                    item_tmpl_ids = erp_tmpl_pool.search([
                        ('id', '=', item.product_tmpl_id.id)])
                    if not item_tmpl_ids:
                        _logger.error(
                            'Template ID not found: %s' % item.default_code)

                    # Add extra fields not present in product_product
                    item_tmpl = erp_tmpl_pool.browse(item_tmpl_ids[0])     

                    data = {                        
                        # TODO check with if the company fields
                        
                        # ----------------
                        # Template fields:
                        # ----------------
                        'weight_net': item_tmpl.weight_net,
                        # purchase_ok
                        # sale_ok
                        # seller_id seller_ids seller_qty
                        #uom_id, uom_po_id, uos_coeff, uos_id
                        
                        # --------------
                        # Product fields
                        # --------------
                        # All company
                        'colour': item.colour,
                        'categ_id': categ_id or 1, # NOTE: mandatory
                        'colls': item.colls,
                        'colls_number': item.colls_number,
                        'default_code': item.default_code,
                        'description': item.description,
                        'description_web': item.description_web,
                        'ean13': item.ean13,
                        'fabric': item.fabric,
                        'height': item.height,
                        'large_description': item.large_description,
                        'length': item.length,
                        'linear_length': item.linear_length,
                        'mexal_id': item.mexal_id,
                        'name': name,
                        'price': item.price,
                        'price_extra': item.price_extra,
                        'quantity_x_pack': item.quantity_x_pack,
                        'q_x_pack': item.q_x_pack,
                        'width': item.width,
                        'weight': item.weight,
                        'weight_net': item.weight_net,
                        #'best_cost': item.best_cost,
                        #category_id > web.category
                        ##'code': item.code,
                        #'color_id': item.color_id, > web.color
                        #'default_photo': item.default_photo,
                        #'default_supplier': item.default_supplier, # no!?!
                        #'default_supplier_code': item.default_supplier_code,
                        #'duty_id > product_custom_duty
                        #'first_code': item.first_code,
                        #'first_supplier': item.first_supplier,
                        #'fixed_margin': item.fixed_margin,
                        ##ERR'H_pack': item.H_pack,
                        #'import': item.import,
                        #'incoming_qty': item.incoming_qty,
                        #'line_id > web.line
                        ##'lst_price': ': item.lst_price,
                        #'location_id': item.location_id,
                        ##ERR'L_pack': item.L_pack,
                        ##ERR'manual_price': item.manual_price,
                        ##name_template
                        #'outoing_qty': item.outoing_qty,
                        #'partner_ref': item.partner_ref,
                        ##ERR'P_pack': item.P_pack,
                        #'preview': item.preview,
                        #'pricelist_id': item.pricelist_id,
                        ##ERR NON PRES'price_margin': item.price_margin,
                        ##product_tmpl_id
                        ##'project_id': item.project_id,
                        #'qty_available': item.qty_available,
                        #'quotation_photo': item.quotation_photo,
                        #'tipology_id > web.tipology
                        #'track_incoming': item.track_incoming,
                        #'track_outgoing': item.track_outgoing,
                        #'track_production': item.track_production,
                        ##ERR'transpost_packaging_usd': 
                        ##    item.transpost_packaging_usd,
                        ##'type': 'service',
                        #'type_of_material': item.type_of_material,
                        #'valuation': item.valuation,
                        #'variants': item.variants,
                        #'virtual_available': item.virtual_available,
                        ##ERR NON PRES'vm_description': item.vm_description,
                        ##ERR NON PRES'vm_name': item.vm_name,
                        ##ERR NON PRES'vm_short': item.vm_short,
                        ##ERR NON PRES'web': item.web,
                        #'web_image_create_time': item.web_image_create_time,
                        #'web_image_preview': item.web_image_preview,
                        #'web_image_update': item.web_image_update,
                        
                        # No Amazon, no K2 fields                        

                        # Extra fields:
                        'description_purchase': item.description_purchase,
                        'description_sale': item.description_sale,
                        'sql_import': item.mexal_id, # for sync purpose
                        'migration_old_id': item.id,
                        'list_price': item.list_price,
                        'standard_price': item.standard_price,
                        'volume': item.volume,
                        'warranty': item.warranty,                        

                        # Link:
                        'migration_old_tmpl_id': item.product_tmpl_id.id,
                        }

                    if 'extra_description' in dir(item): # First company (extra fields):
                        data.update({
                            # No source field:
                            'extra_description': item_tmpl.extra_description,
                            'weight_packaging': item_tmpl.weight_packaging,
                            'telaio': item_tmpl.telaio,                        
                            'colour_code': item_tmpl.colour_code,
                            'dim_article': item_tmpl.dim_article,
                            'dim_pack': item_tmpl.dim_pack,
                            'dim_pallet': item_tmpl.dim_pallet,
                            'item_per_box': item_tmpl.item_per_box,
                            'item_per_camion': item_tmpl.item_per_camion,
                            'item_per_mq': item_tmpl.item_per_mq,
                            'item_per_pallet': item_tmpl.item_per_pallet,
                            'pipe_diameter': item_tmpl.pipe_diameter,
                            'pack_l': item_tmpl.pack_l,
                            'pack_h': item_tmpl.pack_h,
                            'pack_p': item_tmpl.pack_p,

                            # No destination field:
                            'dimension_text': item.dimension_text,
                            'error_dimension': item.error_dimension,
                            'dazi': item.dazi,
                            'dazi_eur': item.dazi_eur,
                            'error_import': item.error_import,
                            'fob_cost_supplier': item.fob_cost_supplier,
                            'fob_cost_supplier_eur': item.fob_cost_supplier_eur,
                            'fob_cost_total': item.fob_cost_total,
                            'fob_cost_total_eur': item.fob_cost_total_eur,
                            'fob_pricelist': item.fob_pricelist,
                            'fob_pricelist_compute': item.fob_pricelist_compute,
                            'fob_pricelist_compute_eur': 
                                item.fob_pricelist_compute_eur,
                            'in_pricelist': item.in_pricelist,
                            'margin': item.margin,
                            'transport_packaging': item.transport_packaging,
                            })

                    # Note: search by code (default_code is the key)
                    new_ids = item_pool.search(cr, uid, [
                        ('default_code', '=', item.default_code)],
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                            print i, "#INFO ", obj, "update:", \
                                item.default_code
                        else:
                            print i, "#INFO ", obj, "jumped:", \
                                item.default_code
                        converter[item.id] = item_id
                    else: # Create
                        if wiz_proxy.create:
                            converter[item.id] = item_pool.create(cr, uid, data,
                                context=context)
                            print i, "#INFO", obj, " create:", item.default_code
                except:
                    print i, "#ERR", sys.exc_info()
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            # Automatic load:
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

            # Manual load with default_code:
            if not self._converter['product.product']:
                # Convert using default code
                item_pool = self.pool.get(obj)
                erp_pool = erp.ProductProduct
                item_ids = erp_pool.search([])
                for item in erp_pool.browse(item_ids):
                    default_code = item.default_code
                    new_ids = item_pool.search(cr, uid, [
                        ('default_code', '=', default_code)], context=context)

                    if new_ids: 
                        if len(new_ids) > 1:
                            _logger.warning(
                                 'Multi product code: %s' % default_code)
                                 
                        item_pool.write(cr, uid, new_ids, {
                            'migration_old_id': item.id, 
                            }, context=context)
                        self._converter['product.product'][
                            item.id] = new_ids[0]
                    else:
                        _logger.error(
                             'Product not found code: %s' % default_code)

            # Load template converter:
            self._converter['product.template'] = {}            
            product_ids = self.pool.get('product.product').search(
                cr, uid, [], context=context)            
            for product in self.pool.get('product.product').browse(cr, uid, 
                    product_ids, context=context):
                # Save in converter dict:    
                self._converter['product.template'][
                    product.migration_old_tmpl_id] = product.product_tmpl_id.id


        # ---------------------------------------------------------------------
        # product.packaging
        # ---------------------------------------------------------------------
        # TODO remove
        '''
        obj = 'product.packaging' 
        product_pool = self.pool.get('product.product') # for extra use
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.package:
            item_pool = self.pool.get(obj)
            erp_pool = erp.ProductPackaging
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    product_id = self._converter['product.product'].get(
                            item.product_id.id, False)
                    if not product_id:
                        _logger.error('Product ID not found!: %s' % (
                            item.product_id.id, ))
                        continue    
                    product_proxy = product_pool.browse(
                        cr, uid, product_id, context=context)
                    ul = self._converter['product.ul'].get(item.ul.name, False)   
                    if not ul:
                        _logger.error('UL not present!')
                        continue
                            
                    data = {
                        'ul': ul, # product.ul
                        'code': item.code,
                        'product_tmpl_id': product_proxy.product_tmpl_id.id,
                        'weight': item.weight, 
                        'sequence': item.sequence,
                        'ul_qty': item.ul_qty,
                        'ean': item.ean,
                        'qty': item.qty,
                        'rows': item.rows,
                        'name': name,

                        #'container_id' # base.container.type >> ul_container
                        
                        # Moved in product.ul (for now insert also here)
                        'width': item.width,
                        'length': item.length,
                        'height': item.height,
                        'weight_ul': item.weight_ul,
                        
                        'q_x_container': item.q_x_container,                        
                        'dimension_text': item.dimension_text,
                        'error_dimension_pack': item.error_dimension_pack,
                        'pack_volume': item.pack_volume,
                        'pack_volume_manual': item.pack_volume_manual,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                     #converter[item.id] = item_id # not used
                except:
                    print "#ERR", obj, "jumped:", name
                    print sys.exc_info()
                    continue                    
        else: # Load convert list form database
            #self.load_converter(cr, uid, converter, obj=obj,
            #     context=context)
            pass # not used converter
        
        # ---------------------------------------------------------------------
        # mrp.bom
        # ---------------------------------------------------------------------
        obj = 'mrp.bom' 
        product_pool = self.pool.get(obj)
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.bom:
            item_pool = self.pool.get(obj)
            erp_pool = erp.MrpBom
            item_ids = erp_pool.search([
                ('bom_id', '=', False)]) # parent before
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    uom_name = item.product_uom.name
                    if uom_name == 'Pz': # rename
                        uom_name = 'Unit(s)'

                    # Many2one:
                    routing_id = False
                    # No routing in DB
                    #self._converter[ # mrp.routing 
                    #    'mrp.routing'].get(item.routing_id.id, False) 
                    product_uom = self._converter[ # product.uom
                        'product.uom'].get(uom_name, False)
                        
                    product_id = self._converter[ # product.product
                        'product.product'].get(item.product_id.id, False)
                    tmpl_id = self._converter[ # mrp.bom
                        'product.template'].get(item.product_id.id, False)

                    data = {
                        # not null:
                        'product_efficiency': item.product_efficiency, 
                        'name': name,
                        'type': item.type,
                        'product_qty': item.product_qty,
                        
                        'date_stop': item.date_stop,
                        'code': item.code,
                        'sequence': item.sequence,
                        'active': item.active,
                        'product_rounding': item.product_rounding,
                        'date_start': item.date_start,
                        'position': item.position,
                        'obsolete': item.obsolete,
                        'old_cost': item.old_cost,
                        'tot_component': item.tot_component,
                        'note': item.note,

                        'routing_id': routing_id, 
                        'product_uom': product_uom, 
                        'product_id': product_id, 
                        'migration_old_id': item.id,
                        #'company_id'

                        # only in odoo:
                        'product_tmpl_id': tmpl_id, # product.template
                        # family
                        # obsolete

                        # only in v. 6.0
                        #'product_uos_qty': item.product_uos_qty,
                        #'product_uos': product_uos, # product.uos
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id 
                except:
                    #print "#ERR", obj, "jumped:", name
                    print sys.exc_info()
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        obj = 'mrp.bom.line' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.bomline:
            item_pool = self.pool.get(obj)
            erp_pool = erp.MrpBom
            item_ids = erp_pool.search([
                ('bom_id', '!=', False)]) # component
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.id # theres' no name here
                    
                    uom_name = item.product_uom.name
                    if uom_name == 'Pz': # rename
                        uom_name = 'Unit(s)'

                    product_uom = self._converter[ # product.uom
                        'product.uom'].get(uom_name, False)
                        
                    routing_id = False
                    # No routing in DB
                    #self._converter[ # mrp.routing 
                    #    'mrp.routing'].get(item.routing_id.id, False) 

                    product_id = self._converter[ # product.product
                        'product.product'].get(item.product_id.id, False)
                    if not product_id:
                        _logger.error('BOM product not found ID: %s' % name)
                        continue    

                    bom_id = self._converter[ # mrp.bom
                        'mrp.bom'].get(item.bom_id.id, False)
                    if not bom_id:
                        _logger.error('BOM parent not found: %s' % name)
                        continue    

                    data = {
                        'date_stop': item.date_stop,
                        'product_uom': product_uom, 
                        'sequence': item.sequence,
                        'date_start': item.date_start,
                        'routing_id': routing_id, 
                        'product_rounding': item.product_rounding,
                        'product_qty': item.product_qty,
                        'product_efficiency': item.product_efficiency, 
                        'type': item.type,
                        'bom_id': bom_id,
                        'product_id': product_id, 
                        #'product_uos': product_uos, # product.uos
                        #'company_id'
                        'migration_old_id': item.id,

                        'obsolete': item.obsolete,
                        'note': item.note,
                        #'old_cost': item.old_cost, # calculated!
                        #'tot_component': item.tot_component,
                        
                         # ODOO only: 
                         # product_uos_qty

                         # v.6 only:
                         # note
                         # code
                         # active
                         # name
                         # company_id
                         # position
                         # tot_component
                         # obsolete
                         # old_cost
                         }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                     #converter[item.id] = item_id # not used
                except:
                    print "#ERR", obj, "jumped:", name
                    print sys.exc_info()
                    continue                    
        else: # Load convert list form database
            #self.load_converter(cr, uid, converter, obj=obj,
            #     context=context)
            pass # no needed
            
        # ---------------------------------------------------------------------
        # Pricelist
        # ---------------------------------------------------------------------

        obj = 'product.pricelist' # linked by mexal_id key (only create dict)
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        # Always loaded
        item_pool = self.pool.get(obj)
        erp_pool = erp.ProductPricelist
        item_ids = erp_pool.search([])
        for item in erp_pool.browse(item_ids):
            # TODO problem with item.mexal_id!!!
            if 'mexal_id' in dir(item):
                mexal_id = item.mexal_id
            else:
                mexal_id = item.name.split('[')[-1].split(']')[0]
                if not '.' in mexal_id:            
                    _logger.error('Cannot find mexal ID %s' % item.name)
                    continue
                if 'Listino Mexal n. ' in mexal_id:
                    mexal_id = mexal_id[-1]    
            new_ids = item_pool.search(cr, uid, [
                ('mexal_id', '=', mexal_id)], context=context)
            if new_ids: # Modify
                item_id = new_ids[0]
                converter[item.id] = item_id
            else: # No creation here
                print "#ERR", obj, "not found:", mexal_id
                
        obj = 'product.pricelist.version' # linked by mexal_id key (for dict)
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        # Always loaded
        item_pool = self.pool.get(obj)
        erp_pool = erp.ProductPricelistVersion
        item_ids = erp_pool.search([])
        for item in erp_pool.browse(item_ids):
            # TODO problem with item.mexal_id!!!
            if 'mexal_id' in dir(item):
                mexal_id = item.mexal_id
            else:    
                mexal_id = item.name.split('[')[-1].split(']')[0]
                if not '.' in mexal_id and 'Versione base ' not in mexal_id:
                    _logger.error('Cannot find mexal ID %s' % item.name)
                    continue
                if 'Versione base ' in mexal_id:
                    mexal_id = mexal_id[-1]    

            new_ids = item_pool.search(cr, uid, [
                ('mexal_id', '=', mexal_id)], context=context)
            if new_ids: # Modify
                item_id = new_ids[0]
                converter[item.id] = item_id
            else: # Create
                _logger.warning("%s not found: %s" % ( obj, mexal_id))

        # Load pricelist:      
        if wiz_proxy.purchase or wiz_proxy.purchase_line:
            pl_pool = self.pool.get('product.pricelist')
            item_ids = pl_pool.search(cr, uid, [('type', '=', 'purchase')])
            if item_ids:
                purchase_pricelist_id = item_ids[0]
            else:
                _logger.warning("No sale pricelist found")
                purchase_pricelist_id = 0

        # ---------------------------------------------------------------------
        # statistic.category
        # ---------------------------------------------------------------------
        obj = 'statistic.category' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # Load with partner (use name non ID)
        if wiz_proxy.partner and not wiz_proxy.link:
            item_pool = self.pool.get(obj)
            erp_pool = erp.StatisticCategory
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try:
                    # Create record to insert/update
                    name = item.name
                    data = {'name': name}
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", obj, "jumped:", name
                    continue
        ''' # TODO removed
        # ---------------------------------------------------------------------
        # res.partner and res.partner.address
        # ---------------------------------------------------------------------
        obj = 'res.partner'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # for use same name  
        self._converter['res.partner.address'] = {} # For destinations!
              
        # ------------------------------------------------
        # Syncro partner without update other informations
        # ------------------------------------------------
        # Link when there's a sync in the midle (create structure from 6 to 8)
        item_pool = self.pool.get(obj) #

        if wiz_proxy.partner and wiz_proxy.link:
            erp_pool = erp.ResPartner
            item_ids = erp_pool.search([
                '|', ('mexal_c', '!=', False), ('mexal_s', '!=', False)]) 
            i = 0    
            for item in erp_pool.browse(item_ids):
                try:
                    i += 1
                    if i % 100 == 0:
                        print "%s partner record imported" % i
                    if item.mexal_c:
                        domain = [('sql_customer_code', '=', item.mexal_c)]
                    elif item.mexal_s: # TODO maybe unwanted substitution?
                        [('sql_supplier_code', '=', item.mexal_s)]
                    else:    
                        print "Not found: %s %s" % (item.mexal_c, item.mexal_c)
                        continue
                        
                    # Write:                        
                    partner_ids = item_pool.search(cr, uid, domain)
                    if partner_ids:
                        item_id = partner_ids[0]
                        item_pool.write(cr, uid, item_id, {
                            'migration_old_id': item.id}, context=context)
                except:
                    print i, "#ERR", obj, "jump:", item.name, sys.exc_info()
                    continue

            erp_pool = erp.ResPartnerAddress
            item_ids = erp_pool.search([
                '|', ('mexal_c', '!=', False), ('mexal_s', '!=', False)]) 
            i = 0    
            for item in erp_pool.browse(item_ids):
                try:
                    i += 1
                    if i % 100 == 0:
                        print "%s address record imported" % i
                    if item.mexal_c:
                        domain = [('sql_destination_code', '=', item.mexal_c)]
                    elif item.mexal_s:
                        domain = [('sql_destination_code', '=', item.mexal_s)]
                    else:
                        print "Not found: %s %s" % (mexal_c, mexal_c)
                        continue    
                    
                    partner_ids = item_pool.search(
                        cr, uid, domain, context=context)                        
                    if len(partner_ids) > 1:
                        print "Too much destination: %s %s" % (
                            item.mexal_c, item.mexal_s)
                    if partner_ids:
                        item_id = partner_ids[0]
                        item_pool.write(cr, uid, item_id, {
                            'migration_old_id': item.id,
                            }, context=context)
                    else:
                        print "Not found: %s %s" % (item.mexal_c, item.mexal_c) 
                except:
                    print i, "#ERR", obj, "jump:", item.name, sys.exc_info()
                    continue
        
        # ------------------------------------
        # Syncro partner with all informations
        # ------------------------------------
        if wiz_proxy.partner and not wiz_proxy.link:
            # -----------------------------------------------------------------
            # A. Searching for partner (master):
            # -----------------------------------------------------------------
            item_pool = self.pool.get(obj)
            erp_pool = erp.ResPartner
            item_ids = erp_pool.search([]) 
            i = 0
            
            try:
                statistic_category_id = self._converter[
                    'statistic.category'].get(
                        item.statistic_category_id.id, False)
            except:
                statistic_category_id = False                
                
            for item in erp_pool.browse(item_ids):
                try:
                    i += 1                                        
                    name = item.name.strip()
                    # Create record to insert / update
                    data = { # NOTE: partner are imported add only new data
                        'active': item.active,
                        # No: (address)
                        #article_label_id > easylabel.label
                        'city': item.city,
                        'comment': item.comment,
                        ##company_id
                        #country
                        #credit_limit
                        'customer': item.customer,
                        'date': item.date,
                        'date_last_ddt': item.date_last_ddt,
                        'day_left_ddt': item.day_left_ddt,
                        'ddt_e_oc_c': item.ddt_e_oc_c,
                        'ddt_e_oc_s': item.ddt_e_oc_s,
                        'debit_limit': item.debit_limit,
                        'discount_rates': item.discount_rates,
                        'discount_value': item.discount_value,
                        'ean13': item.ean13,
                        'email': item.email,
                        #employee bool
                        'fido_date': item.fido_date,
                        'fido_ko': item.fido_ko,
                        'fido_total': item.fido_total,
                        #fiscal_id_code
                        #import
                        #invoice_agent_id
                        #invoiced_current_year
                        #invoice_last_year
                        #lang
                        #last_reconviliation_date
                        'mexal_note': item.mexal_note,
                        'mexal_c': item.mexal_c,
                        'mexal_s': item.mexal_s,
                        'mobile': item.mobile,
                        'name': name,
                        #order_current_year
                        #order_last_year
                        #pack_label_id easylabel.label
                        #pallet_label_id easylabel.label
                        ##parent_id
                        #partner_color
                        #partner_importante_id
                        'phone': item.phone,
                        #private
                        #property_account_position
                        #property_payment_term
                        #property_product_pricelist # TODO pricelist
                        #property_product_pricelist_purchase
                        #property_stock_customer
                        #property_stock_supplier
                        'ref': item.ref,
                        #saldo_c
                        #saldo_s
                        #section_id crm.case.section # TODO source / campaign
                        'statistic_category_id': statistic_category_id,
                        'supplier': item.supplier,
                        #title
                        'trend': item.trend,
                        'trend_category': item.trend_category,
                        'type_cei': item.type_cei,
                        #type_id  crm.case.resource.type
                        'user_id': self._converter['res.users'].get(
                            item.user_id.id if item.user_id else False, False),
                        'vat': item.vat,
                        #vat_subject
                        'website': item.website,
                        #zone_id  res.partner.zone # TODO zone

                        # New fieds:
                        'is_company': True,
                        'is_address': False,
                        'sql_customer_code': item.mexal_c,
                        'sql_supplier_code': item.mexal_s,
                        'migration_old_id': item.id,
                        # ??
                        #'notify_email': item.nofify_email,
                        #'opt_out': item.opt_out,

                        # Conversione of IDs
                        #'': self._convert(
                        #    'crm.tracking.campaign').get(
                        #        item.type_id, False),
                        }

                        # TODO mexal data di creazione da importare

                    # Pre SQL import:
                    partner_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)])
                    if partner_ids:
                        item_id = partner_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                            print i, "#INFO", obj, "update:", item.name
                        else:
                            print i, "#INFO", obj, "jumped:", item.name
                    else: # Create
                        item_id = item_pool.create(
                            cr, uid, data, context=context)
                        print i, "#INFO", obj, "create:", item.name
                    converter[item.id] = item_id
                except:
                    print data
                    print i, "#ERR", obj, "jump:", item.name, sys.exc_info()
                    continue

            # -----------------------------------------------------------------
            # B. Searching for partner address (default address):
            # -----------------------------------------------------------------
            item_pool = self.pool.get('res.partner')
            erp_pool = erp.ResPartnerAddress

            # Destination address:
            item_ids = erp_pool.search([
                ('mexal_c', '=', False), ('mexal_s', '=', False)])

            for item in erp_pool.browse(item_ids): # TODO stopped!!!
                try:
                    partner_id = converter.get(item.id, False)
                    if not partner_id:
                        _logger.error("Parent not found: %s" % item.id)
                        continue
                    # Create record to insert / update
                    data = { # NOTE: partner are imported add only new data
                        # function
                        # type
                        #'partner_id': partner_id,
                        'street': address.street,
                        'street2': address.street2,
                        'fax': address.fax,
                        'phone': address.phone,
                        'mobile': address.mobile,
                        # country!! state_id
                        'city': address.city,
                        'zip': address.zip,
                        'email': address.email,
                        #'birthdate': address.birthdate,
                        #'title': address,
                        #'migration_old_id': item.id,
                        }

                    # Read info from address related to this partner:
                    partner_ids = item_pool.search(cr, uid, [
                        ('id', '=', partner_id)])
                    if partner_ids:
                        if wiz_proxy.update:
                            item_id = item_pool.write(cr, uid, partner_ids,
                                data)
                            print "#INFO", obj, "partner-addr upd:", \
                                item.partner_id.name
                    else: # Create
                        print "#ERR", obj ,"partner-addr not found", \
                            item.partner_id.name
                    converter[item.id] = item_id

                except:
                    print "#ERR", obj, "jumped:", item.id
                    continue
                # NOTE No contact for this database

            # -----------------------------------------------------------------
            # C. Searching for partner address (destination):
            # -----------------------------------------------------------------
            item_pool = self.pool.get('res.partner') #
            erp_pool = erp.ResPartnerAddress
            # Destination address:
            item_ids = erp_pool.search([
                '|', ('mexal_c','!=', False), ('mexal_s','!=', False)])
            for item in []:# erp_pool.browse(item_ids): # TODO stopped!!!
                try:
                    partner_id = self._converter['res.partner'].get(
                        item.id, False) # TODO test error
                    name = item.name.strip()
                    # Create record to insert / update
                    data = { # NOTE: partner are imported add only new data
                        # type parent_id category vat_subjected
                        # function
                        # type
                        'partner_id': partner_id,
                        'is_address': True,
                        'active': item.active,
                        'sql_destination_code': item.mexal_d,
                        'street': address.street,
                        'street2': address.street2,
                        'fax': address.fax,
                        'phone': address.phone,
                        'mobile': address.mobile,
                        # country!! state_id
                        'city': address.city,
                        'zip': address.zip,
                        'email': address.email,
                        'birthdate': address.birthdate,
                        #'title': address,
                        'migration_old_id': item.id,
                        }

                    # Read info from address related to this partner:
                    address_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id), ])
                    if address_ids:
                        if wiz_proxy.update:
                            item_id = item_pool.write(cr, uid, address_ids,
                                data, )
                            print "#INFO", obj, "(dest) upd:", item.name
                        else:
                            print "#INFO", obj, "(dest) jump:", item.name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj ,"(dest) create:", item.name
                    converter[item.id] = item_id

                except:
                    _logger.error(sys.exc_info())
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            # Not use load_converter but splitted loop c/s and dest.
            item_ids = item_pool.search(cr, uid, [], context=context)
            for item in item_pool.browse(cr, uid, item_ids, context=context):
                if not item.migration_old_id:
                    continue # jump line
                if item.is_address:
                    self._converter['res.partner.address'][
                        item.migration_old_id] = item.id
                    
                else:    
                    self._converter['res.partner'][
                        item.migration_old_id] = item.id

        # ---------------------------------------------------------------------
        #                               EASY LABEL
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # easylabel.easylabel
        # ---------------------------------------------------------------------
        '''
        obj = 'easylabel.easylabel' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelEasylabel
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                            
                    data = {
                        'name': name,
                        'path': item.path,
                        'command': item.command,
                        'oerp_command': item.oerp_command,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)
            
        # ---------------------------------------------------------------------
        # easylabel.path
        # ---------------------------------------------------------------------
        obj = 'easylabel.path' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelPath
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                            
                    data = {
                        'name': name,
                        'path': item.path,
                        'note': item.note,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # easylabel.label
        # ---------------------------------------------------------------------
        obj = 'easylabel.label' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelLabel
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    root_id = self._converter['easylabel.path'].get(
                        item.root_id.id, False)
                    
                    data = {
                        'name': name,
                        'label_name': item.label_name,
                        'height': item.height,
                        'width': item.width,
                        'lot': item.lot,
                        'folder': item.folder,
                        'root_id': root_id,
                        #'path_id': path_id, # related
                        'type': item.type,
                        'counter': item.counter,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # easylabel.parameter
        # ---------------------------------------------------------------------
        obj = 'easylabel.parameter' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelParameter
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    label_id = self._converter['easylabel.label'].get(
                        item.label_id.id, False)
                    
                    data = {
                        'name': name,
                        'sequence': item.sequence,
                        'label_id': label_id,
                        'mode': item.mode,
                        'mode_type': item.mode_type,
                        'value': item.value,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # easylabel.batch
        # ---------------------------------------------------------------------
        obj = 'easylabel.batch' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelBatch
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    data = {
                        'name': name,
                        'date': item.date,
                        'state': item.state,
                        'line': item.line,
                        'week': item.week,
                        'note': item.note,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # easylabel.particularity
        # ---------------------------------------------------------------------
        # TODO not for all 2 company!!!
        obj = 'easylabel.particularity' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelParticularity
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    try:    
                        partner_id = self._converter['res.partner'].get(
                            item.partner_id.id, False)
                    except:
                        partner_id = False

                    try:    
                        article_label_id = self._converter[
                            'easylabel.label'].get(
                                item.article_label_id.id, False)
                    except:
                        article_label_id = False
                        
                    try:    
                        pack_label_id = self._converter[
                            'easylabel.label'].get(
                                item.pack_label_id.id, False)
                    except:
                        pack_label_id = False
                        
                    try:    
                        pallet_label_id = self._converter[
                            'easylabel.label'].get(
                                item.pallet_label_id.id, False)
                    except:
                        pallet_label_id = False
                    
                    data = {
                        'name': name,
                        'partner_id': partner_id,
                        'article_label_id': article_label_id,
                        'pack_label_id': pack_label_id,
                        'pallet_label_id': pallet_label_id,
                        #'partner_name': item.partner_name,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # easylabel.printer
        # ---------------------------------------------------------------------
        obj = 'easylabel.printer' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelPrinter
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    data = {
                        'name': name,
                        'number': item.number,
                        'sequence': item.sequence,
                        'type': item.type,
                        'note': item.note,
                        'migration_old_id': item.id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # easylabel.batch.line
        # ---------------------------------------------------------------------
        # TODO not for all 2 company!!!
        obj = 'easylabel.batch.line' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.easylabel:
            item_pool = self.pool.get(obj)
            erp_pool = erp.EasylabelBatchLine
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    
                    try:    
                        batch_id = self._converter['easylabel.batch'].get(
                            item.batch_id.id, False)
                    except:
                        batch_id = False
                        
                    try:    
                        printer_id = self._converter['easylabel.printer'].get(
                            item.printer_id.id, False)
                    except:
                        printer_id = False

                    try:    
                        partner_id = self._converter['res.partner'].get(
                            item.partner_id.id, False)
                    except:
                        partner_id = False

                    try:    
                        product_id = self._converter['product.product'].get(
                            item.product_id.id, False)
                    except:
                        product_id = False

                    try:    
                        label_id = self._converter['easylabel.label'].get(
                            item.label_id.id, False)
                    except:
                        label_id = False
                    
                    data = {
                        'name': name,
                        'sequence': item.sequence,
                        'position': item.position,
                        'total': item.total,
                        'type': item.type,
                        'shipment': item.shipment,
                        'shipment_date': item.shipment_date,
                        'order': item.order,
                        'order_c': item.order_c,

                        # Many2one fileds:
                        'batch_id': batch_id,
                        'printer_id': printer_id,
                        'partner_id': partner_id,
                        'product_id': product_id,                        
                        'label_id': label_id,
                        
                        'migration_old_id': item.id,
                        
                        # Related:
                        #'package_id': item.package_id, 
                        #'article_label_id': item.article_label_id,
                        #'pack_label_id': item.pack_label_id,
                        #'pallet_label_id': item.pallet_label_id,
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                     #converter[item.id] = item_id # not used
                except:
                    _logger.error("%s Error sync: %s" % (obj, name))
                    _logger.error("%s" % (sys.exc_info(), ))
                    continue                    
        else: # Load convert list form database
            #self.load_converter(cr, uid, converter, obj=obj,
            #     context=context)
            pass
        ''' # TODO remove
        
        # ---------------------------------------------------------------------
        # product.supplierinfo
        # ---------------------------------------------------------------------
        obj = 'product.supplierinfo' 
        item_pool = self.pool.get('product.supplierinfo')
        product_pool = self.pool.get('product.product')
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.supplierinfo:
            item_pool = self.pool.get(obj)
            erp_pool = erp.ProductSupplierinfo
            item_ids = erp_pool.search([])
            _logger.info('Total supplierinfo: %s' % len(item_ids))
            i = 0
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    i += 1
                    name = item.name.id # partner_id
                    partner_id = self._converter['res.partner'].get(
                            name, False)
                    if not partner_id:
                        _logger.error('Partner ID not found!: %s' % (
                            name, ))
                        continue
                    
                    tmpl_id = self._converter['product.template'].get(
                        item.product_id.id, False)
                                                        
                    if not tmpl_id:
                        _logger.error('Product template ID not found!: %s' % (
                            item.product_id, ))
                        continue
                        
                    data = {
                        'name': partner_id,
                        'sequence': item.sequence,
                        'qty': item.qty,
                        'delay': item.delay,
                        'min_qty': item.min_qty,
                        'product_code': item.product_code,
                        'product_name': item.product_name,
                        'product_tmpl_id': tmpl_id,
                        'migration_old_id': item.id, 
                        'product_uom': self._converter[
                            'product.uom'].get(
                                item.product_uom.id \
                                    if item.product_uom \
                                    else False, False),
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                            _logger.info("%s. %s update: %s" % (i, obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s. %s create: %s" % (i, obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s. %s jumped: %s" % (i, obj, name))
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)

        # ---------------------------------------------------------------------
        # pricelist.partnerinfo (update only date)
        # ---------------------------------------------------------------------
        obj = 'pricelist.partnerinfo' 
        item_pool = self.pool.get(obj)
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.partnerinfo:
            item_pool = self.pool.get(obj)
            erp_pool = erp.PricelistPartnerinfo
            item_ids = erp_pool.search([])
            _logger.info('Total supplierinfo: %s' % len(item_ids))
            i = 0
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    i += 1
                    name = item.name
                    data = {
                        'date_quotation': item.date_quotation,
                        'min_quantity': item.min_quantity,
                        'price': item.price,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # only update:
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context={'without_history': True})
                        _logger.info("%s. %s update: %s" % (i, obj, name))
                except:
                    _logger.error("%s. %s jumped: %s" % (i, obj, name))
                    _logger.error(sys.exc_info())
                    continue                    
        return True # TODO pricelist importation ******************************


        # ---------------------------------------------------------------------
        # pricelist.partnerinfo
        # ---------------------------------------------------------------------
        # TODO error in company 1
        obj = 'pricelist.partnerinfo' 
        item_pool = self.pool.get(obj)
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.partnerinfo:
            item_pool = self.pool.get(obj)
            erp_pool = erp.PricelistPartnerinfo
            item_ids = erp_pool.search([])
            _logger.info('Total supplierinfo: %s' % len(item_ids))
            i = 0
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    i += 1
                    name = item.name
                    suppinfo_id = self._converter['product.supplierinfo'].get(
                        item.suppinfo_id.id, False)
                        
                    if not suppinfo_id:
                        _logger.error('Suppinfo ID not found!: %s' % name)
                        continue # jump

                    tmpl_id = self._converter['product.template'].get(
                        item.product_id.id, False)
                    
                    data = {
                        'suppinfo_id': suppinfo_id,
                        'min_quantity': item.min_quantity,
                        'price': item.price,
                        'name': name, 
                        'migration_old_id': item.id,
                        
                        # not present in ODOO:
                        'date_quotation': item.date_quotation,
                        'is_active': item.is_active,
                        'product_id': tmpl_id,
                        }
                    if 'price_usd' in dir(item):
                        data['price_usd'] = item.price_usd

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s. %s update: %s" % (i, obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s. %s create: %s" % (i, obj, name))

                    converter[item.id] = item_id # not used
                except:
                    _logger.error("%s. %s jumped: %s" % (i, obj, name))
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                 context=context)
        return True # TODO pricelist importation ******************************
        
        # ---------------------------------------------------------------------
        # account.payment.term
        # ---------------------------------------------------------------------
        obj = 'account.payment.term' # TODO also for english
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale or wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.AccountPaymentTerm
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    data = {
                        'name': item.name,
                        'note': item.note,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id
                except:
                    _logger.error(sys.exc_info())
                    continue
                    
        else: # Load convert list form database
            pass # Non used (no migration_old_id)
            #self.load_converter(cr, uid, converter, obj=obj,
            #    context=context)

        # ---------------------------------------------------------------------
        # stock.incoterms
        # ---------------------------------------------------------------------
        obj = 'stock.incoterms' # TODO also for english
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale or wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.StockIncoterms
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    code = item.code
                    name = item.name                    
                    data = {
                        'name': name,
                        'active': item.active,
                        'code': code,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('code', '=', code)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id
                except:
                    _logger.error(name)
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            pass # Non used (no migration_old_id)
            #self.load_converter(cr, uid, converter, obj=obj,
            #    context=context)

        # ---------------------------------------------------------------------
        # sale.product.return
        # ---------------------------------------------------------------------
        obj = 'sale.product.return' # TODO also for english
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale or wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.SaleProductReturn
            error = False
            try:
                item_ids = erp_pool.search([])
            except:
                error = True
                _logger.warning('Object: %s not found in v. 6.0 (jump)' % obj)
            if not error:                    
                for item in erp_pool.browse(item_ids):
                    try: # Create record to insert/update
                        name = item.name                    
                        data = {
                            'name': name,
                            'text': item.text,
                            }
                        new_ids = item_pool.search(cr, uid, [
                            ('name', '=', name)], context=context)
                        if new_ids: # Modify
                            item_id = new_ids[0]
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                            _logger.info("%s update: %s" % (obj, name))
                        else: # Create
                            item_id = item_pool.create(cr, uid, data,
                                context=context)
                            _logger.info("%s create: %s" % (obj, name))
                        _logger.info("%s create: %s" % (obj, name))

                        converter[item.id] = item_id
                    except:
                        _logger.info("%s jumped: %s" % (obj, name))
                        _logger.info(sys.exc_info())
                        continue                    
        else: # Load convert list form database
            pass # Non used (no migration_old_id)
            #self.load_converter(cr, uid, converter, obj=obj,
            #    context=context)
        
        # ---------------------------------------------------------------------
        # sale.product.return
        # ---------------------------------------------------------------------
        obj = 'sale.order.bank' # TODO also for english
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale or wiz_proxy.sale_line: # << loaded only here 
            item_pool = self.pool.get(obj)
            erp_pool = erp.SaleOrderBank
            try:
                item_ids = erp_pool.search([])
            except:
                error = True
                _logger.warning('Object: %s not found in v. 6.0 (jump)' % obj)
            if not error:
                for item in erp_pool.browse(item_ids):
                    try: # Create record to insert/update
                        name = item.name                    
                        data = {
                            'name': name,
                            'information': item.information,
                            }
                        new_ids = item_pool.search(cr, uid, [
                            ('name', '=', name)], context=context)
                        if new_ids: # Modify
                            item_id = new_ids[0]
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                            _logger.info("%s update: %s" % (obj, name))
                        else: # Create
                            item_id = item_pool.create(cr, uid, data,
                                context=context)
                            _logger.info("%s create: %s" % (obj, name))

                        converter[item.id] = item_id
                    except:
                        _logger.error(sys.exc_info())
                        continue                    
                    
        # ---------------------------------------------------------------------
        # account.fiscal.position
        # ---------------------------------------------------------------------
        obj = 'account.fiscal.position' # TODO also for english
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale or wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.AccountFiscalPosition
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name                    
                    data = {
                        'name': name,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.warning("%s error, here not create!: %s" % (
                            obj, name))

                    converter[item.id] = item_id
                except:
                    _logger.error(sys.exc_info())
                    continue                    
                
        # ---------------------------------------------------------------------
        # sale.order
        # ---------------------------------------------------------------------
        obj = 'sale.order'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale:
            item_pool = self.pool.get(obj)
            erp_pool = erp.SaleOrder
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    data = {
                        'name': item.name,
                        'note': item.note,
                        'date_order': item.date_order,
                        'client_order_ref': item.client_order_ref,
                        'origin': item.origin,
                        'create_date': item.create_date,
                        'user_id': self._converter[
                            'res.users'].get(
                                item.user_id.id \
                                    if item.user_id \
                                    else False, False),
                        'payment_term': self._converter[
                            'account.payment.term'].get(
                                item.payment_term.id \
                                    if item.payment_term \
                                    else False, False),
                        'incoterm': self._converter[
                            'stock.incoterms'].get(
                                item.incoterm.id \
                                    if item.incoterm \
                                    else False, False),
                        'picking_policy': item.picking_policy, # direct one
                        'order_policy': item.order_policy, # manual picking ...
                        'fiscal_position': self._converter[
                            'account.fiscal.position'].get(
                                item.fiscal_position.id \
                                    if item.fiscal_position \
                                    else False, False),
                        'partner_id': self._converter[
                            'res.partner'].get(
                                item.partner_id.id \
                                    if item.partner_id \
                                    else False, 1),                                    
                        'migration_old_id': item.id,                        
                        'destination_partner_id': self._converter[
                            'res.partner.address'].get(
                                item.partner_shipping_id.id \
                                    if item.partner_shipping_id \
                                    else False, False),
                        # TODO:
                        #'confirm_date': item.confirm_date, # Not present
                        }
                        
                    # ---------------------------------------------    
                    # Extra fields not present in all installation:    
                    # ---------------------------------------------    
                    if 'quotation_model' in dir(item):                
                        data['quotation_model'] = item.quotation_model
                        
                    if 'return_id' in dir(item):                
                        return_id  = self._converter['sale.product.return'].get(
                        item.return_id.id if item.return_id else False, False)
                        data['return_id'] = return_id
                    
                    if 'bank_id' in dir(item):
                        bank_id = self._converter['sale.order.bank'].get(
                        item.bank_id.id if item.bank_id else False, False)
                        data['bank_id'] = bank_id
                    
                    # For problem in pricelist (if not present) TODO test
                    pricelist_id = self._converter['product.pricelist'].get(
                        item.pricelist_id.id if item.pricelist_id else False, 
                        1) # TODO set default pricelist 1 (remove and update with partner)
                    if pricelist_id:
                        data['pricelist_id'] = pricelist_id
                        
                        
                    new_ids = item_pool.search(cr, uid, [
                        #('name', '=', name)], context=context) #use migrateID ?
                        ('migration_old_id', '=', item.id)], context=context) #use migrateID ?
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    converter[item.id] = item_id
                except:
                    _logger.error(sys.exc_info())
                    continue
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

        # ---------------------------------------------------------------------
        # sale.order.line
        # ---------------------------------------------------------------------
        obj = 'sale.order.line'        
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        default_product_uom = 1 # Pz.
        if wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.SaleOrderLine
            item_ids = erp_pool.search([])

            for item in sock.execute(openerp.name, user_id, 
                    openerp.password, obj, 'read', item_ids):
                try: # Create record to insert/update
                    name = item['name']
                    try:
                        order_id = self._converter['sale.order'][
                            item['order_id'][0]]
                    except:
                        _logger.error("Order ID not present: %s" % name)                        
                        continue

                    old_id = item['id']
                    data = {
                        'name': item['name'],
                        #'note': item['note'], # TODO both company? 1?
                        'order_id': order_id,
                        'sequence': item['sequence'],
                        'product_id': self._converter['product.product'].get(
                                item['product_id'][0] \
                                    if type(item['product_id']) == list \
                                    else False, False),
                        'price_unit': item['price_unit'],
                        'product_uom': self._converter[
                            'product.uom'].get(
                                item['product_uom'][0] \
                                    if type(item['product_uom']) == list \
                                    else False, default_product_uom),
                        'product_uos': self._converter[
                            'product.uom'].get(
                                item['product_uom'] \
                                    if type(item['product_uos']) == list \
                                    else False, default_product_uom),
                        'product_uom_qty': item['product_uom_qty'],
                        'product_uos_qty': item['product_uos_qty'],
                        'discount': item['discount'],
                        'th_weight': item['th_weight'],
                        'delay': item['delay'],
                        
                        # Extxra fields:
                        'discount': item['discount'],
                        'migration_old_id': old_id,

                        # TODO used?!?
                        #'address_allotment_id': 'res.partner'
                        #'company_id'
                        #'state': item.state,                        
                        }
                    try:      
                        data['tax_id'] = [
                            (6, 0, (self._converter['account.tax'][
                                item['tax_id'][0]], ))]
                    except:
                        _logger.warning("Error reading tax for line (not set)")
                    try:
                        data['multi_discount_rates'] = item[
                            'multi_discount_rates']
                            
                        data['price_use_manual'] = item['price_use_manual']
                        data['price_unit_manual'] = item['price_unit_manual']
                    except:
                        pass    

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', old_id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        _logger.info("%s update: %s" % (obj, name))
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        _logger.info("%s create: %s" % (obj, name))

                    #converter[old_id] = item_id # No needed!
                    # TODO if state is order: wizard confirm!!!
                except:
                    _logger.error(name)
                    _logger.error("#ERR %s jumped: %s [%s]" % (
                        obj, name, sys.exc_info()))
                    continue
        else: # Load convert list form database
            pass # Non used

        # ---------------------------------------------------------------------
        # stock.location
        # ---------------------------------------------------------------------
        obj = 'stock.location' 
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.purchase or wiz_proxy.purchase_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.StockLocation
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name                  
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context)
                    if new_ids: # Modify
                        converter[item.id] = new_ids[0]
                        print "#INFO", obj, "linked:", name
                    else: # Create
                        print "#ERR", obj, "not found:", name

                except:
                    print "#ERR", obj, "jumped:", name
                    print sys.exc_info()
                    continue                    

        # ---------------------------------------------------------------------
        # purchase.order
        # ---------------------------------------------------------------------
        obj = 'purchase.order'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.purchase:
            item_pool = self.pool.get(obj)
            erp_pool = erp.PurchaseOrder
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    data = {
                        'name': item.name,
                        'date_order': item.date_order,
                        'partner_ref': item.partner_ref,
                        'origin': item.origin,
                        #'create_date': item.create_date,
                        #'user_id': self._converter[
                        #    'res.users'].get(
                        #        item.user_id.id \
                        #            if item.user_id \
                        #            else False, False),
                        #'payment_term': self._converter[
                        #    'account.payment.term'].get(
                        #        item.payment_term.id \
                        #            if item.payment_term \
                        #            else False, False),
                        #'quotation_model': item.quotation_model,
                        #'incoterm': self._converter[
                        #    'stock.incoterms'].get(
                        #        item.incoterm.id \
                        #            if item.incoterm \
                        #            else False, False),
                        #'picking_policy': item.picking_policy, # direct one
                        #'order_policy': item.order_policy, # manual picking ...
                        #'return_id': self._converter[
                        #    'sale.product.return'].get(
                        #        item.return_id.id \
                        #            if item.return_id \
                        #            else False, False),
                        #'bank_id': self._converter[
                        #    'sale.order.bank'].get(
                        #        item.bank_id.id \
                        #            if item.bank_id \
                        #            else False, False),                        
                        #'fiscal_position': self._converter[
                        #    'account.fiscal.position'].get(
                        #        item.fiscal_position.id \
                        #            if item.fiscal_position \
                        #            else False, False),
                        #'pricelist_id': self._converter[
                        #    'product.pricelist'].get(
                        #        item.pricelist_id.id \
                        #            if item.pricelist_id \
                        #            else False, False),
                        'partner_id': self._converter[
                            'res.partner'].get(
                                item.partner_id.id \
                                    if item.partner_id \
                                    else False, 1),                                    
                        'migration_old_id': item.id,
                        #'destination_partner_id': self._converter[
                        #    'res.partner'].get(
                        #        item.partner_shipping_id.id \
                        #            if item.partner_shipping_id \
                        #            else False, False),
                        'payment_note': item.payment_note,
                        'delivery_note': item.delivery_note,
                        'pricelist_id': purchase_pricelist_id,
                        #'note': item.note,

                        # TODO:
                        #'confirm_date': item.confirm_date, # Not present
                        }

                    location_id = self._converter[
                            'stock.location'].get(
                                item.location_id.id \
                                    if item.location_id \
                                    else False, False)
                    if not location_id:
                        _logger.error('Location not found, jumped')
                        continue
                    data['location_id'] = location_id

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context) 
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(
                            cr, uid, data, context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    _logger.error(sys.exc_info())
                    continue
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

        # ---------------------------------------------------------------------
        # purchase.order.line
        # ---------------------------------------------------------------------
        obj = 'purchase.order.line'        
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        default_product_uom = 1 # Pz.
        if wiz_proxy.purchase_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.PurchaseOrderLine
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    try:
                        order_id = self._converter['purchase.order'][
                            item.order_id.id]
                    except:
                        _logger.error("Order ID not present: %s" % name)                        
                        continue

                    data = {
                        'name': item.name,
                        'note': item.note, # TODO both company? 1?
                        #'sequence': item.sequence,
                        'product_id': self._converter[
                            'product.product'].get(
                                item.product_id.id \
                                    if item.product_id \
                                    else False, False),
                        'price_unit': item.price_unit,
                        'product_uom': self._converter[
                            'product.uom'].get(
                                item.product_uom.id \
                                    if item.product_uom \
                                    else False, default_product_uom),
                        #'product_uos': self._converter[
                        #    'product.uom'].get(
                        #        item.product_uom.id \
                        #            if item.product_uos \
                        #            else False, default_product_uom),
                        'product_qty': item.product_qty,
                        #'product_uos_qty': item.product_uos_qty,
                        #'discount': item.discount,
                        #'th_weight': item.th_weight,
                        #'delay': item.delay,
                        
                        # Extxra fields:
                        #'multi_discount_rates': item.multi_discount_rates,
                        #'price_use_manual': item.price_use_manual,
                        #'price_unit_manual': item.price_unit_manual,
                        #'discount': item.discount,
                        'date_planned': item.date_planned,

                        'migration_old_id': item.id,

                        # TODO used?!?
                        #'address_allotment_id': 'res.partner'
                        #'company_id'
                        #'state': item.state,                        
                        }
                    try:
                        data['taxes_id'] = [(6, 0, (tax_22a, ))] # NOTE add 22
                    except:
                        pass # use default tax

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                    # TODO if state is order: wizard confirm!!!
                except:
                    _logger.error(name)
                    _logger.error("#ERR %s jumped: %s [%s]" % (
                        obj, name, sys.exc_info()))
                    print sys.exc_info()
                    continue
        else: # Load convert list form database
            pass # Non used
            #self.load_converter(cr, uid, converter, obj=obj,
            #    context=context)

        
        # ---------------------------------------------------------------------
        #                        CUSTOM FOR THIS PARTNER
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # auto.stock.supplier
        # ---------------------------------------------------------------------
        """obj = 'auto.stock.supplier' # no need converter
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.autostock:
            item_pool = self.pool.get(obj)
            erp_pool = erp.AutoStockSupplier
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name                    
                    data = {
                        'name': name,
                        'suspended': item.suspended,
                        'migration_old_id': item.id,                        
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        new_ids = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name
                except:
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)"""

        # END:
        return True

    _columns = {
        'name': fields.char('Source DB name', size=80, required=True),
        'hostname': fields.char('Source Hostname', size=80, required=True),
        'port': fields.integer('Source Port', required=True),
        'username': fields.char('Source Username', size=80, required=True),
        'password': fields.char('Source Password', size=80, required=True),
        }

# -----------------------------------------------------------------------------
# Add reference for future update of migration / sync
# -----------------------------------------------------------------------------
class ResUsers(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class CrmTrackingCampaign(orm.Model):
    _inherit = 'crm.tracking.campaign'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class AutoStockReport(orm.Model):
    _inherit = 'auto.stock.supplier'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        'migration_old_address_id': fields.integer('ID v.6'),
        }

class ProductProduct(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        'migration_old_tmpl_id': fields.integer('ID tmpl v.6'),
        }


class ProductCategory(orm.Model):
    _inherit = 'product.category'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ProductPricelist(orm.Model):
    _inherit = 'product.pricelist'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ProductPricelistVersion(orm.Model):
    _inherit = 'product.pricelist.version'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class SaleOrderLine(orm.Model):
    _inherit = 'sale.order.line'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class MrpBom(orm.Model):
    _inherit = 'mrp.bom'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class MrpBomLine(orm.Model):
    _inherit = 'mrp.bom.line'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class PurchaseOrder(orm.Model):
    _inherit = 'purchase.order'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class PurchaseOrderLine(orm.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ProductTemplate(orm.Model):
    _inherit = 'product.template'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ResPartnerCategory(orm.Model):
    _inherit = 'res.partner.category'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ProductSupplierinfo(orm.Model):
    _inherit = 'product.supplierinfo'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class PricelistPartnerinfo(orm.Model):
    _inherit = 'pricelist.partnerinfo'         

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class ProductPackaging(orm.Model):
    _inherit = 'product.packaging'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class EasylabelEasylabel(orm.Model):
    _inherit = 'easylabel.easylabel'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class EasylabelPath(orm.Model):
    _inherit = 'easylabel.path'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class EasylabelLabel(orm.Model):
    _inherit = 'easylabel.label'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class EasylabelParameter(orm.Model):
    _inherit = 'easylabel.parameter'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class EasylabelBatch(orm.Model):
    _inherit = 'easylabel.batch'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }

class EasylabelParticularity(orm.Model):
    _inherit = 'easylabel.particularity'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }
        
class EasylabelPrinter(orm.Model):
    _inherit = 'easylabel.printer'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }
        
class EasylabelBatchLine(orm.Model):
    _inherit = 'easylabel.batch.line'

    _columns = {
        'migration_old_id': fields.integer('ID v.6'),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:class ResPartnerCategory(orm.Model):
