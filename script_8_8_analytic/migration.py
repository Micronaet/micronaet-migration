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

class SyncroXMLRPCAccount(orm.Model):
    ''' Function for migration (and setup parameters for XMLRPC)
        So no file .cfg to setup
    '''
    _name = 'syncro.xmlrpc.account'

    _converter = {}

    def load_converter(self, cr, uid, converter, obj,
            field_id='account_old_id', context=None):
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
        ''' Migrate account production
        '''

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
        user_id = sock.login(
            openerp.name, 
            openerp.username, 
            openerp.password,
            )
        sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (
            openerp.hostname,
            openerp.port), allow_none=True)
        
        from_date = wiz_proxy.from_date or False
        to_date = wiz_proxy.to_date or False

        # ---------------------------------------------------------------------
        #          SIMPLE OBJECT (LOAD OR CREATE)  << ALWAYS RUN
        # ---------------------------------------------------------------------

        # TODO Create Product

        # TODO Create Employee

        # ---------------------------------------------------------------------
        # res.users >> res.users >> (product.product) (hr.employee)
        # ---------------------------------------------------------------------
        obj = 'res.users'
        #obj_out = 'res.users'
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
                        'account_old_id': item.id,
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
        # product.category
        # ---------------------------------------------------------------------
        obj_old = 'product.category'
        obj = 'account.analytic.account'
        self._converter[obj] = {}
        _logger.info("Start %s" % obj)
        converter = self._converter[obj]
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
                        'account_parent_old_id': item.id,
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
            
        # ---------------------------------------------------------------------
        # product.product
        # ---------------------------------------------------------------------
        obj_old = 'product.product'
        obj = 'account.analytic.account'
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
                    i += 1
                    data = {                        
                        'name': item.name,
                        'account_old_id': item.id,
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
                        converter[item.id] = item_id
                    else: # Create
                        if wiz_proxy.create:
                            converter[item.id] = item_pool.create(cr, uid, data,
                                context=context)
                            print i, "#INFO", obj, " create:", item.default_code
                except:
                    print i, "#ERR", sys.exc_info()
                    continue
        else: # Load convert list form database
            # Automatic load:
            self.load_converter(cr, uid, converter, obj=obj,
                context=context)

# -----------------------------------------------------------------------------
# Add reference for future update of migration / sync
# -----------------------------------------------------------------------------
# Uses Employee Product:
class ResUsers(orm.Model):
    _inherit = 'res.users'
    # res.users > product.product
    # res.users > res.employee (link product)
    # res.users > res.users (link employee)

    _columns = {
        'account_old_id': fields.integer('Account migration ID'),
        }

class HrEmployee(orm.Model):
    _inherit = 'hr.employee'
    # res.users > product.product
    # res.users > res.employee (link product)

    _columns = {
        'account_old_id': fields.integer('Account migration ID'),
        }

class ProductProduct(orm.Model):
    _inherit = 'product.product'
    # res.users > product.product

    _columns = {
        'account_old_id': fields.integer('Account migration ID'),
        }


class ResPartner(orm.Model):
    _inherit = 'res.partner'
    # account.analyitic.account > res.parner

    _columns = {
        # Analytic account:
        'account_old_id': fields.integer('Account migration ID'),
        }

class AccountAnaliticAccount(orm.Model):
    _inherit = 'account.analitic.account'
    # product.category > account.analitic.account 
    # product.product > account.analitic.account (with parent ID)

    _columns = {
        # Product:
        'account_old_id': fields.integer('Account migration ID'),
        # Category:
        'account_parent_old_id': fields.integer('Account parent migration ID'),
        }

class AccountAnaliticLine(orm.Model):
    _inherit = 'account.analitic.line'
    # account.analitic.line > account.analitic.line

    _columns = {
        'account_old_id': fields.integer('Account migration ID'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:class ResPartnerCategory(orm.Model):
