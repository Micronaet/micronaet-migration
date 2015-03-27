# -*- coding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
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
    ''' Function for migration (and setup parameters for XMLRPC
    '''
    _name = 'syncro.xmlrpc'

    _converter = {}

    # TODO change:
    journal_id = 3 # TS
    to_invoice = 1 # Sì 100%
    categ_all = 1
    general_account_id = 146
    
    def load_converter(self, cr, uid, converter, table, 
            field_id='migration_old_id', context=None):
        ''' Load coverter if not present
        '''
        item_pool = self.pool.get(table)
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
        '''

        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def get_hr_category(self, cr, uid, item, context=context):
            ''' Search category or create if not present
            '''
            try:
                name = item[1]
                category_pool = self.pool.get('hr.employee.category')
                category_ids = category_pool.search(cr, uid, [
                    ('name', '=', name)], context=context)
                if category_ids:
                    return category_ids[0]    
                return category_pool.create(cr, uid, {
                    'name': name, }, context=context)    
            except:
               print "#ERR Create employee category:", sys.exc_info()
               return False    
                
        def get_product_category(self, cr, uid, item, context=context):
            ''' Search category or create if not present
            '''
            try:
                name = item[1]
                category_pool = self.pool.get('product.category')
                category_ids = category_pool.search(cr, uid, [
                    ('name', '=', name)], context=context)
                if category_ids:
                    # TODO remove
                    category_pool.write(cr, uid, category_ids, {
                        'parent_id': self.categ_all, 
                        }, context=context)
                    return category_ids[0]    
                return category_pool.create(cr, uid, {
                    'name': name, 
                    'parent_id': self.categ_all,
                    }, context=context)    
            except:
               print "#ERR Create employee category:", sys.exc_info()
               return False    

        def get_product_category_account(self, cr, uid, item, context=context):
            ''' Search category or create if not present (version correct not
                used)
            '''
            try:
                name = item[1]
                category_pool = self.pool.get('account.analytic.account')
                category_ids = category_pool.search(cr, uid, [
                    ('name', '=', name),
                    ('type', '=', 'view'),
                    ], context=context)
                if category_ids:
                    return category_ids[0]    
                return category_pool.create(cr, uid, {
                    'name': name, 
                    'type': 'view',
                    }, context=context)    
            except:
               print "#ERR Create employee category (account):", sys.exc_info()
               return False    

        # ---------------------------------------------------------------------
        # Common part: connection
        # ---------------------------------------------------------------------
        # First record only
        item_ids = self.search(cr, uid, [], context=context)
        if not item_ids:
           return False

        openerp = self.browse(cr, uid, item_ids[0], context=context)

        sock = xmlrpclib.ServerProxy(
            'http://%s:%s/xmlrpc/common' % (
                openerp.hostname,
                openerp.port,
                ), allow_none=True)

        uid_old = sock.login(
            openerp.name,
            openerp.username,
            openerp.password, )

        sock = xmlrpclib.ServerProxy(
            'http://%s:%s/xmlrpc/object' % (
                openerp.hostname,
                openerp.port,
                ), allow_none=True)

        # ---------------------------------------------------------------------
        # res.users
        # ---------------------------------------------------------------------
        table = 'res.users'
        
        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.user:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    # Create record to insert / update
                    data = {
                        'name': item['name'],
                        'login': item['login'],
                        'active': item['active'],
                        'signature': item['signature'],
                        }
                    if 'admin' != item['login']:
                        data['password'] = item['password']

                    new_ids = item_pool.search(cr, uid, [
                        ('login', '=', item['login'])],  # search login
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", table, "update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", item['name']

                    # Write always the ID
                    item_pool.write(cr, uid, item_id, {
                        'migration_old_id': item['id'],
                        }, context=context)
                    converter[item['id']] = item_id
                except:
                    print "#ERR", table, "jumped:", item['name']
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table, 
                context=context)

        # ---------------------------------------------------------------------
        # res.partner and res.partner.address
        # ---------------------------------------------------------------------
        table = 'res.partner'
        table2 = 'res.partner.address'

        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.partner:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    name = item['name'].strip()
                    # Create record to insert / update
                    data = {
                        'name': name,
                        'date': item['date'],
                        'comment': item['comment'],
                        'ean13': item['ean13'],
                        'ref': item['ref'],
                        'website': item['website'],
                        'customer': item['customer'],
                        'supplier': item['supplier'],
                        'is_company': True,
                        'fiscalcode': item['x_fiscalcode'],
                        # type parent_id category vat_subjected
                        'vat': item['vat'],
                        #'notify_email': item.nofify_email,
                        #'opt_out': item.opt_out,
                        'is_address': False,
                        'active': item['active'],
                        #lang
                        }

                    # Read info from address related to this partner:                    
                    address_ids = sock.execute(
                        openerp.name, uid_old, openerp.password,
                        table2, 'search', [('partner_id', '=', item['id'])])
                    if address_ids:
                        address_read = sock.execute(openerp.name, uid_old,
                            openerp.password, table2, 'read', address_ids)
                        address = address_read[0]
                        data.update({
                            # function
                            # type
                            'street': address['street'],
                            'street2': address['street2'],
                            'fax': address['fax'],
                            'phone': address['phone'],
                            'mobile': address['mobile'],
                            # country!! state_id
                            'city': address['city'],
                            'zip': address['zip'],
                            'email': address['email'],
                            'birthdate': address['birthdate'],
                            #'title': address,
                            })

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item['id'])],
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO",table ," update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        item_pool.write(cr, uid, item_id, {
                            'migration_old_id': item['id'],
                            }, context=context)
                        print "#INFO",table ,"create:", item['name']

                    converter[item['id']] = item_id

                    # Teste if there's more than one address
                    if len(address_ids) > 1:
                        print "+ Address:", item['name'], len(address_ids)
                        # TODO create other addresses: (here not present)

                except:
                    print "#ERR", table, "jumped:", item['name']
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table, 
                context=context)

        # ---------------------------------------------------------------------
        # hr.employee
        # ---------------------------------------------------------------------
        table = 'hr.employee'

        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.employee:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    # Create record to insert / update
                    data = {
                        'name': item['name'],
                        'active': item['active'],
                        'birthday': item['birthday'],
                        'work_email': item['work_email'],
                        'gender': item['gender'],
                        #'mobile_phone': item['mobile_phone'],
                        'work_location': item['work_location'],
                        'parent_id': self._converter[
                            'hr.employee'].get(item['id'], False), # Parent TODO 2 times
                        'notes': item['notes'],
                        'marital': item['marital'].replace(
                            'maried', 'married').replace('other', 'single'),
                        #product_id  journal_id
                        }
                        
                    if not item['user_id']:
                        print "#ERR no user ID", item['name']    
                        continue
                        #data['user_id'] = 19 # TODO Boniotti Clara
                    else:    
                        data['user_id'] = self._converter['res.users'][
                            item['user_id'][0]]
                            
                    # category_id now category_ids
                    if item['category_id']: 
                        data['category_ids'] = [
                            (6, 0, [get_hr_category(self, cr, uid, 
                            item['category_id'], context=context)])]
    
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item['id'])],
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", table, "update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", item['name']

                    # Write always the ID
                    item_pool.write(cr, uid, item_id, {
                        'migration_old_id': item['id'],
                        }, context=context)
                    converter[item['id']] = item_id
                except:
                    print "#ERR", table, item['name'], sys.exc_info()
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table, 
                context=context)

        # ---------------------------------------------------------------------
        # hr.attendance
        # ---------------------------------------------------------------------
        table = 'hr.attendance'

        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.attendance:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    # Create record to insert / update
                    if not item['employee_id']:
                        print "#ERR empty employee ID"
                        continue
                    data = {
                        'name': item['name'],
                        'employee_id': self._converter[
                            'hr.employee'].get(item['employee_id'][0], False),
                        'action': item['action'],
                        }

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item['id'])],
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", item, " update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, " create:", item['name']

                    # Write always the ID
                    item_pool.write(cr, uid, item_id, {
                        'migration_old_id': item['id'],
                        }, context=context)
                    converter[item['id']] = item_id
                except:
                    print "#ERR", table, item['name'], sys.exc_info()
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table, 
                context=context)

        # ---------------------------------------------------------------------
        # product.product
        # ---------------------------------------------------------------------
        table = 'product.product' # template??
        self._converter[table] = {}
        converter = self._converter[table]
        if wiz_proxy.product:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    # PARENT analytic account:
                    categ_id = get_product_category(
                        self, cr, uid, item[
                            'categ_id'], context=context)
                            
                    # Create record to insert / update
                    data = {
                        'name': item['name'],
                        'default_code': item['default_code'],
                        'categ_id': categ_id,                        
                        'type': 'service',
                        'standard_price': 1.0,
                        'list_price': 1.0,
                        }

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item['id'])],
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO ", table, "update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, " create:", item['name']
                        item_pool.write(cr, uid, item_id, {
                            'migration_old_id': item['id'],
                            }, context=context)
                    converter[item['id']] = item_id
                except:
                    print "#ERR", table, item['name'], sys.exc_info()
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table, 
                context=context)

        # ---------------------------------------------------------------------
        # account.analytic.account
        # ---------------------------------------------------------------------
        table = 'account.analytic.account'  # partner

        self._converter[table] = {} 
        converter = self._converter[table]
        if wiz_proxy.account:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:                    
                    # Create record to insert / update
                    data = {
                        'name': item['name'],
                        'type': 'normal',
                        #'parent_id': categ_id,
                        'code': item['code'],
                        'use_timesheets': True,
                        }
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item['id'])],
                            context=context)                            
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", table, "update:", item['name']
                    else: # search by name
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#WARN", table, " create:", item['name']
                            
                    # Save ID created for future update        
                    item_pool.write(cr, uid, item_id, {
                        'migration_old_id': item['id'],
                        }, context=context)
                                    
                    converter[item['id']] = item_id
                except:
                    print "#ERR", table, item['name'], sys.exc_info()
        else: # Load convert list form database
            self.load_converter(
                cr, uid, converter, table=table, context=context)

        # ---------------------------------------------------------------------
        # hr.analytic.timesheet
        # ---------------------------------------------------------------------
        table = 'hr.analytic.timesheet' 
        
        if wiz_proxy.line:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [
                    ('date', '>=', '2015/01/01'),
                    ('date', '<', '2016/01/01'),])

            # load ad conversion:
            #conversion_dict = {}
            #for element in self.pool.get('hr.analytic.timesheet').browse(
            #        cr, uid, item_ids, context=context):
            #    if element.migration_old_id:
            #        conversion_dict[element.migration_old_id] = element.id
                
            i = 0
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    i += 1
                    # Find foreign keys:
                    if item['user_id']:
                        user_id = self._converter[
                           'res.users'].get(item['user_id'][0], False)
                    else:
                        user_id = False # error
                        
                    # product > search in account
                    if item['product_id']: # account_id
                        product_id = self._converter[
                           'product.product'].get(item[
                               'product_id'][0], False)
                    else:
                        product_id = False # error
                        
                    # account > search in partner
                    if item['account_id']: # res.partner
                        account_id = self._converter[
                           'account.analytic.account'].get(item[
                               'account_id'][0], False)
                    else:
                        account_id = False # error
                                
                    # Create record to insert / update
                    data = {
                        'name': item['name'],
                        'user_id': user_id,
                        'date': item['date'],
                        'account_id': account_id,
                        'unit_amount': item['unit_amount'],
                        'amount': item['amount'],
                        'to_invoice': self.to_invoice, #item['to_invoice'],
                        #'ts_partner_id': ts_partner_id,    
                        'product_id': product_id,
                        'journal_id': self.journal_id,                    
                        'general_account_id': self.general_account_id,
                        }

                    #new_ids = [conversion_dict.get(item['id'], False)]
                    #new_ids = item_pool.search(cr, uid, [
                    #    ('migration_old_id', '=', item['id'])],
                    #        context=context)
                    #if new_ids: # Modify
                    #    item_id = new_ids[0]
                    #    item_pool.write(cr, uid, item_id, data,
                    #        context=context)
                    #    print "#INFO", i, table, "update:", item['name']
                    #else: # Create
                    item_id = item_pool.create(cr, uid, data,
                        context=context)
                    print "#INFO", i, table, " create:", item['id']
                    item_pool.write(cr, uid, item_id, {
                        'migration_old_id': item['id'],
                        }, context=context)
                except:
                    print "#ERR", table, item['name'], sys.exc_info()
                # NOTE No contact for this database


        # ---------------------------------------------------------------------
        # hr.holiday (firs hr.holiday.status)
        # ---------------------------------------------------------------------
        # -------------------------
        table = 'hr.holidays.status'
        # -------------------------
        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.holiday:
            # Load table first:
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    # Create record to insert / update
                    data = {'name': item['name']}
                    new_ids = item_pool.search(cr, uid, [
                        ('name', '=', item['name'])], context=context)
                    if new_ids:
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", table, "update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", item['name']
                    converter[item['id']] = item_id
                except:
                    print "#ERR", table, "jumped:", item['name']
                # NOTE No contact for this database
        
            # ------------------
            table = 'hr.holidays'
            # ------------------            
            self._converter[table] = {} # TODO used
            converter = self._converter[table] # for use same name
            item_pool = self.pool.get(table)
            item_ids = sock.execute(
                openerp.name, uid_old, openerp.password, table, 'search', [])
            for item in sock.execute(openerp.name, uid_old,
                    openerp.password, table, 'read', item_ids):
                try:
                    holiday_status_id = False # TODO
                    # Create record to insert / update
                    data = {
                        'name': item['name'],
                        'holiday_status_id': self._converter[
                            'hr.holidays.status'].get(
                                item['holiday_status'][0], False),
                        'date_from': item['date_from'],
                        'date_to': item['date_to'],
                        'employee_id': self._converter[
                            'hr.employee'].get(item['employee_id'][0], False),
                        #'department_it': False,
                        'holiday_type': 'employee',
                        }
                        
                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item['id'])],  # search name
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        item_pool.write(cr, uid, item_id, data,
                            context=context)
                        print "#INFO", table, "update:", item['name']
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", item['name']

                    # Write always the ID
                    item_pool.write(cr, uid, item_id, {
                        'migration_old_id': item['id'],
                        }, context=context)
                except:
                    print "#ERR", table, "jump:", item['name'], sys.exc_info()

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
        'migration_old_id': fields.integer('ID v.8'),
        }

class ResPartner(orm.Model):

    _inherit = 'res.partner'

    _columns = {
        'migration_old_id': fields.integer('ID v.8'),
        'migration_old_account_id': fields.integer(
            'ID account v.8',
            help='Old account id that is new partner ID',
            ),
        }

class HrEmpoyee(orm.Model):

    _inherit = 'hr.employee'

    _columns = {
        'migration_old_id': fields.integer('ID v.8'),
        }
        
class HrAttendance(orm.Model):
    ''' Attendance sign in / sign out
    '''

    _inherit = 'hr.attendance'

    _columns = {
        'migration_old_id': fields.integer('ID v.8'),
        }

class ProductProduct(orm.Model):
    ''' Not used: product are account
    '''

    _inherit = 'product.product'

    _columns = {
        'migration_old_id': fields.integer('ID v.8'),
        }

class ProductTemplate(orm.Model):
    ''' Not used: product are account
    '''

    _inherit = 'product.template'

    _columns = {
        'migration_old_id': fields.integer('ID v.8'),
        }

class AccountAnalyticAccount(orm.Model):
    ''' product.product > account.analytic.account
    '''

    _inherit = 'account.analytic.account'

    _columns = {
        'migration_old_id': fields.integer(
            'ID v.8', 
            help='Link to product.product'
            ),
        }

class HrAnalyticTimesheet(orm.Model):

    _inherit = 'hr.analytic.timesheet'

    _columns = {
        'migration_old_id': fields.integer(
            'ID v.8', ),
        }

class HrHolidays(orm.Model):

    _inherit = 'hr.holidays'

    _columns = {
        'migration_old_id': fields.integer(
            'ID v.8', ),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

