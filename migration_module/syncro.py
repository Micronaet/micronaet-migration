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

# Add reference for future update of migration / sync
class ResPartner(orm.Model):
    _inherit = 'res.partner'

    _columns = {
        'migration_old_id': fields.char('ID v.8', size=15),
        }

class ResUsers(orm.Model):
    _inherit = 'res.users'

    _columns = {
        'migration_old_id': fields.char('ID v.8', size=15),
        }

class SyncroXMLRPC(orm.Model):
    ''' Function for migration (and setup parameters for XMLRPC
    '''
    _name = 'syncro.xmlrpc'

    _converter = {}

    def load_converter(self, cr, uid, table, context=None):
        ''' Load coverter if not present
        '''
        if table not in self._converter:
            self._converter[table] = {}

        table_pool = self.pool.get(table)
            table_ids = table_pool.search(cr, uid, [
                ('migration_old_id', '!=', False)], context=None)
            for table in table_pool.browse(
                    cr, uid, table_ids, context=context):
                self._converter[table][table.migration_old_id] = table.id
        return

    # -------------------------------------------------------------------------
    # Syncro / Migration procedures:
    # -------------------------------------------------------------------------
    def migrate_database(self, cr, uid, wiz_proxy, context=None):
        ''' Module for syncro partner from one DB to another
        '''
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
        if wiz_proxy.user:
            users_pool = self.pool.get('res.users')
            users_ids = sock.execute(
                openerp.name, uid_old, openerp.password,
                'res.users', 'search', [])
            self._converter['res.users'] = {}
            converter = self._converter['res.users'] # for use same name
            for users in sock.execute(openerp.name, uid_old,
                    openerp.password, 'res.users', 'read', users_ids):
                try:
                    # Create record to insert / update
                    data = {
                        'name': users['name'],
                        'login': users['login'],
                        'active': users['active'],
                        'signature': users['signature'],
                        }
                    if 'admin' != users['login']:
                        data['password'] = users['password']

                    new_ids = users_pool.search(cr, uid, [
                        ('login', '=', users['login'])],  # search login
                            context=context)
                    if new_ids: # Modify
                        users_id = new_ids[0]
                        users_pool.write(cr, uid, users_id, data,
                            context=context)
                        print "#INFO users update:", users['name']
                    else: # Create
                        users_id = users_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO users create:", users['name']

                    # Write always the ID
                    users_pool.write(cr, uid, users_id, {
                        'migration_old_id': users['id'],
                        }, context=context)
                    converter[users['id']] = users_id
                except:
                    print "#ERR users jumped:", users['name']
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, 'res.users', context=context)

        # ---------------------------------------------------------------------
        # res.partner and res.partner.address
        # ---------------------------------------------------------------------
        t = 'res.partner'
        t2 = 'res.partner.address'
        if wiz_proxy.partner:
            partner_pool = self.pool.get(t)
            partner_ids = sock.execute(
                openerp.name, uid_old, openerp.password, t, 'search', [])
            self._converter[t] = {}
            converter = self._converter[t] # for use same name
            for partner in sock.execute(openerp.name, uid_old,
                    openerp.password, t, 'read', partner_ids):
                try:
                    # Create record to insert / update
                    data = {
                        'name': partner['name'],
                        'date': partner['date'],
                        'comment': partner['comment'],
                        'ean13': partner['ean13'],
                        'ref': partner['ref'],
                        'website': partner['website'],
                        'customer': partner['customer'],
                        'supplier': partner['supplier'],
                        'is_company': True,
                        'fiscalcode': partner['x_fiscalcode'],
                        # type parent_id category vat_subjected
                        'vat': partner['vat'],
                        #'notify_email': partner.nofify_email,
                        #'opt_out': partner.opt_out,
                        'is_address': False,
                        'active': partner['active'],
                        #lang
                        }

                    # Read info from address related to this partner:
                    address_ids = sock.execute(
                        openerp.name, uid_old, openerp.password,
                        t2, 'search', [('partner_id', '=', partner['id'])])
                    if address_ids:
                        address_read = sock.execute(openerp.name, uid_old,
                            openerp.password, t2, 'read', address_ids)
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

                    new_ids = partner_pool.search(cr, uid, [
                        ('migration_old_id', '=', partner['id'])],
                            context=context)
                    if new_ids: # Modify
                        partner_id = new_ids[0]
                        partner_pool.write(cr, uid, partner_id, data,
                            context=context)
                        print "#INFO",t ," update:", partner['name']
                    else: # Create
                        partner_id = partner_pool.create(cr, uid, data,
                            context=context)
                        partner_pool.write(cr, uid, partner_id, {
                            'migration_old_id': partner['id'],
                            }, context=context)
                        print "#INFO",t ,"create:", partner['name']

                    # Save info for next write of partner_id
                    #if partner.is_address or not partner.is_company:
                    #    # ID v.8 = parent_id v.7
                    #    contact_code[partner_id] = partner.parent_id.id
                    #else: # Partner (save transoce for id 7 > 8
                    #    # Current ID (v.7)            = Other ID (v.8)
                    converter[partner['id']] = partner_id

                    # Teste if there's more than one address
                    if len(address_ids) > 1:
                        print "+ Address:", partner['name'], len(address_ids)
                        # TODO create other addresses: (here not present)

                except:
                    print "#ERR", t, "jumped:", partner['name']
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, 'res.partner', context=context)

        # ---------------------------------------------------------------------
        # hr.attendance
        # ---------------------------------------------------------------------
        t = 'hr.attendance'
        if wiz_proxy.user:
            table_pool = self.pool.get(t)
            table_ids = sock.execute(
                openerp.name, uid_old, openerp.password, t, 'search', [])
            self._converter[t] = {}
            converter = self._converter[t] # for use same name
            for table in sock.execute(openerp.name, uid_old,
                    openerp.password, t, 'read', table_ids):
                try:
                    # Create record to insert / update
                    data = {
                        'name': table['name'],

                        }

                    new_ids = table_pool.search(cr, uid, [
                        ('migration_old_id', '=', table['id'])],
                            context=context)
                    if new_ids: # Modify
                        table_id = new_ids[0]
                        table_pool.write(cr, uid, table_id, data,
                            context=context)
                        print "#INFO",t , " update:", table['name']
                    else: # Create
                        table_id = table_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO",t , " create:", table['name']

                    # Write always the ID
                    table_pool.write(cr, uid, table_id, {
                        'migration_old_id': table['id'],
                        }, context=context)
                    converter[table['id']] = table_id
                except:
                    print "#ERR",t ,"jumped:", table['name']
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, t, context=context)


        return True

    _columns = {
        'name': fields.char('Source DB name', size=80, required=True),
        'hostname': fields.char('Source Hostname', size=80, required=True),
        'port': fields.integer('Source Port', required=True),
        'username': fields.char('Source Username', size=80, required=True),
        'password': fields.char('Source Password', size=80, required=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

