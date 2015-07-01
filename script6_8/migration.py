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
                    data = {                        
                        #'best_cost': item.best_cost,
                        #category_id > web.category
                        'categ_id': categ_id, # NOTE: mandatory
                        ##'code': item.code,
                        'colls': item.colls,
                        'colls_number': item.colls_number,
                        #'color_id': item.color_id, > web.color
                        'colour': item.colour,
                        'colour_code': item.colour_code,
                        'dazi': item.dazi,
                        'dazi_eur': item.dazi_eur,
                        'default_code': item.default_code,
                        #'default_photo': item.default_photo,
                        #'default_supplier': item.default_supplier, # no!?!
                        #'default_supplier_code': item.default_supplier_code,
                        'description': item.description,
                        'description_sale': item.description_sale,
                        'description_purchase': item.description_purchase,
                        'description_web': item.description_web,
                        'dim_article': item.dim_article,
                        'dimension_text': item.dimension_text,
                        'dim_pack': item.dim_pack,
                        'dim_pallet': item.dim_pallet,
                        #'duty_id > product_custom_duty
                        'ean13': item.ean13,
                        'error_dimension': item.error_dimension,
                        'error_import': item.error_import,
                        'extra_description': item.extra_description,
                        'fabric': item.fabric,
                        #'first_code': item.first_code,
                        #'first_supplier': item.first_supplier,
                        #'fixed_margin': item.fixed_margin,
                        'fob_cost_supplier': item.fob_cost_supplier,
                        'fob_cost_supplier_eur': item.fob_cost_supplier_eur,
                        'fob_cost_total': item.fob_cost_total,
                        'fob_cost_total_eur': item.fob_cost_total_eur,
                        'fob_pricelist': item.fob_pricelist,
                        'fob_pricelist_compute': item.fob_pricelist_compute,
                        'fob_pricelist_compute_eur': 
                            item.fob_pricelist_compute_eur,
                        'height': item.height,
                        ##ERR'H_pack': item.H_pack,
                        #'import': item.import,
                        #'incoming_qty': item.incoming_qty,
                        'in_pricelist': item.in_pricelist,
                        'item_per_box': item.item_per_box,
                        'item_per_camion': item.item_per_camion,
                        'item_per_mq': item.item_per_mq,
                        'item_per_pallet': item.item_per_pallet,
                        'large_description': item.large_description,
                        'length': item.length,
                        'linear_length': item.linear_length,
                        #'line_id > web.line
                        ##'lst_price': ': item.lst_price,
                        #'location_id': item.location_id,
                        ##ERR'L_pack': item.L_pack,
                        #'list_price': item.list_price,
                        ##ERR'manual_price': item.manual_price,
                        'margin': item.margin,
                        'mexal_id': item.mexal_id,
                        'name': name,
                        ##name_template
                        #'outoing_qty': item.outoing_qty,
                        'pack_h': item.pack_h,
                        'pack_l': item.pack_l,
                        'pack_p': item.pack_p,
                        #'partner_ref': item.partner_ref,
                        'pipe_diameter': item.pipe_diameter,
                        ##ERR'P_pack': item.P_pack,
                        #'preview': item.preview,
                        'price': item.price,
                        'price_extra': item.price_extra,
                        #'pricelist_id': item.pricelist_id,
                        ##ERR NON PRES'price_margin': item.price_margin,
                        ##product_tmpl_id
                        ##'project_id': item.project_id,
                        #'qty_available': item.qty_available,
                        'quantity_x_pack': item.quantity_x_pack,
                        #'quotation_photo': item.quotation_photo,
                        'q_x_pack': item.q_x_pack,
                        'telaio': item.telaio,
                        #'tipology_id > web.tipology
                        #'track_incoming': item.track_incoming,
                        #'track_outgoing': item.track_outgoing,
                        #'track_production': item.track_production,
                        'transport_packaging': item.transport_packaging,
                        ##ERR'transpost_packaging_usd': 
                        ##    item.transpost_packaging_usd,
                        ##'type': 'service',
                        #'type_of_material': item.type_of_material,
                        ##'standard_price': 1.0,
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
                        'weight_net': item.weight_net,
                        'weight_packaging': item.weight_packaging,
                        'width': item.width,
                        
                        # No Amazon, no K2 fields                        

                        # Extra fields:
                        'sql_import': item.mexal_id, # for sync purpose
                        'migration_old_id': item.id,
                        }

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
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print i, "#INFO", obj, " create:", item.default_code

                    converter[item.id] = item_id
                except:
                    print i, "#ERR", sys.exc_info()
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

        # ---------------------------------------------------------------------
        # Supplier pricelist
        # ---------------------------------------------------------------------
        # TODO?
        
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
                mexal_id = item.mexal_id
                new_ids = item_pool.search(cr, uid, [
                    ('mexal_id', '=', mexal_id)], context=context)
                if new_ids: # Modify
                    item_id = new_ids[0]
                    converter[item.id] = item_id
                else: # Create
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
                mexal_id = item.mexal_id
                new_ids = item_pool.search(cr, uid, [
                    ('mexal_id', '=', mexal_id)], context=context)
                if new_ids: # Modify
                    item_id = new_ids[0]
                    converter[item.id] = item_id
                else: # Create
                    print "#ERR", obj, "not found:", mexal_id
        
        # ---------------------------------------------------------------------
        # res.partner and res.partner.address
        # ---------------------------------------------------------------------
        obj = 'res.partner'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # for use same name
        if wiz_proxy.partner:
            # -----------------------------------------------------------------
            # A. Searching for partner (master):
            # -----------------------------------------------------------------
            item_pool = self.pool.get(obj)
            erp_pool = erp.ResPartner
            item_ids = erp_pool.search([])#[:10]
            i = 0
            
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
                        #statistic_category_id statistic.category # TODO category
                        'supplier': item.supplier,
                        #title
                        'trend': item.trend,
                        'trend_category': item.trend_category,
                        'type_cei': item.type_cei,
                        #type_id  crm.case.resource.type
                        'user_id': self._converter['res.users'].get(
                            item.user_id or 0, False),
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
                            print "#INFO", obj, "partner-addr upd:", item.partner_id.name
                    else: # Create
                        print "#ERR", obj ,"partner-addr not found", item.partner_id.name
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
                '|',('mexal_c','=',True), ('mexal_s','=',True)])
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
                    _logger.error(line)
                    _logger.error(sys.exc_info())
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)
        
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
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    _logger.error(line)
                    _logger.error(sys.exc_info())
                    continue
                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

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
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    _logger.error(line)
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

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
            item_ids = erp_pool.search([])
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
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", obj, "jumped:", name
                    print sys.exc_info()
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)
        
        # ---------------------------------------------------------------------
        # sale.product.return
        # ---------------------------------------------------------------------
        obj = 'sale.order.bank' # TODO also for english
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale or wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.SaleOrderBank
            item_ids = erp_pool.search([])
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
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    _logger.error(line)
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)
                
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
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "Error here I dont' create", name

                    converter[item.id] = item_id
                except:
                    _logger.error(line)
                    _logger.error(sys.exc_info())
                    continue                    
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)
                
        # ---------------------------------------------------------------------
        # sale.order
        # ---------------------------------------------------------------------
        obj = 'sale.order'
        _logger.info("Start %s" % obj)
        update = False
        self._converter[obj] = {}
        converter = self._converter[obj]
        if wiz_proxy.sale: # TODO
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
                        'quotation_model': item.quotation_model,
                        'incoterm': self._converter[
                            'stock.incoterms'].get(
                                item.incoterm.id \
                                    if item.incoterm \
                                    else False, False),
                        'picking_policy': item.picking_policy, # direct one
                        'order_policy': item.order_policy, # manual picking ...
                        'return_id': self._converter[
                            'sale.product.return'].get(
                                item.return_id.id \
                                    if item.return_id \
                                    else False, False),
                        'bank_id': self._converter[
                            'sale.order.bank'].get(
                                item.bank_id.id \
                                    if item.bank_id \
                                    else False, False),                        
                        'fiscal_position': self._converter[
                            'account.fiscal.position'].get(
                                item.fiscal_position.id \
                                    if item.fiscal_position \
                                    else False, False),
                        'pricelist_id': self._converter[
                            'product.pricelist'].get(
                                item.pricelist_id.id \
                                    if item.pricelist_id \
                                    else False, False),

                        # TODO:
                        'partner_id': 1, #'partner_id': item.partner_id.id # TODO Convert
                        'migration_old_id': item.id,
                        #'confirm_date': item.confirm_date, # Not present
                        #'destination_partner_id': item.partner_shipping_id.id # TODO Convert                                                            
                        }

                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', name)], context=context) #use migrateID ?
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                        print "#INFO", obj, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", obj, "create:", name

                    converter[item.id] = item_id
                except:
                    _logger.error(line)
                    _logger.erro(sys.exc_info())
                    continue
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)


        obj = 'sale.order.line'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj]
        import pdb; pdb.set_trace()
        if wiz_proxy.sale_line:
            item_pool = self.pool.get(obj)
            erp_pool = erp.SaleOrderLine
            item_ids = erp_pool.search([])
            for item in erp_pool.browse(item_ids):
                try: # Create record to insert/update
                    name = item.name
                    data = {
                        'name': item.name,
                        'order_id': self._converter[
                            'sale.order'].get(
                                item.order_id.id \
                                    if item.order_id \
                                    else False, False),
                        'sequence': item.sequence, 
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
                                    else False, False),
                        'product_uos': self._converter[
                            'product.uom'].get(
                                item.product_uom.id \
                                    if item.product_uos \
                                    else False, False),
                        'product_uom_qty': item.product_uom_qty,
                        'product_uos_qty': item.product_uos_qty,
                        'discount': item.discount,
                        'th_weight': item.th_weight,
                        'delay': item.delay,
                        
                        # TODO extra fields:
                        
                        # TODO used?!?
                        #'address_allotment_id': 'res.partner'
                        #'company_id'
                        #'state': item.state,                        
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)], context=context)
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
                    _logger.error(line)
                    _logger.error("#ERR %s jumped: %s [%s]" % (
                        obj, name, sys.exc_info()))
                    print sys.exc_info()
                    continue
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)


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
        }

class ProductCategory(orm.Model):
    _inherit = 'product.category'

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
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
