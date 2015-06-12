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
            This method implement some utility function
            and all the selectable function that could be lauched from wizard
        '''

        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
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

        """def get_product_category_account(self, cr, uid, item, context=context):
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
               return False"""

        # ---------------------------------------------------------------------
        # Common part: connection to old database using ERPEEK
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
        # res.users
        # ---------------------------------------------------------------------
        table = 'res.users'
        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.user:
            erp_pool = erp.ResUsers
            item_pool = self.pool.get(table)
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
                        print "#INFO", table, "update:", item.name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", item.name

                    converter[item.id] = item_id
                except:
                    print "#ERR", table, "jumped:", item.name
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table,
                context=context)

        # ---------------------------------------------------------------------
        # crm.tracking.campaign
        # ---------------------------------------------------------------------
        table = 'crm.tracking.campaign'
        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.campaign: # TODO
            item_pool = self.pool.get(table)
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
                        print "#INFO", table, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", table, "jumped:", name
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table,
                context=context)

        # ---------------------------------------------------------------------
        # res.partner.category
        # ---------------------------------------------------------------------
        table = 'res.partner.category' # Tags partner
        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.category: # TODO
            item_pool = self.pool.get(table)
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
                        print "#INFO", table, "update:", name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table, "create:", name

                    converter[item.id] = item_id
                except:
                    print "#ERR", table, "jumped:", name
                    continue
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
            erp_pool = erp.CrmCaseCateg
            item_ids = erp_pool.search([])
            i = 0
            for item in erp_pool.browse(item_ids):
                try:
                    # PARENT analytic account:
                    i += 1
                    categ_id = get_product_category(
                        self, cr, uid, item.categ_id, context=context)

                    # Create record to insert / update
                    data = {
                        'name': item.name,
                        'default_code': item.default_code,
                        'categ_id': categ_id,
                        'type': 'service',
                        'standard_price': 1.0,
                        'list_price': 1.0,
                        'migration_old_id': item.id,
                        }

                    new_ids = item_pool.search(cr, uid, [
                        ('migration_old_id', '=', item.id)],
                            context=context)
                    if new_ids: # Modify
                        item_id = new_ids[0]
                        if wiz_proxy.update:
                            item_pool.write(cr, uid, item_id, data,
                                context=context)
                            print i, "#INFO ", table, "update:", item.name
                        else:
                            print i, "#INFO ", table, "jumped:", item.name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print i, "#INFO", table, " create:", item.name
                    converter[item.id] = item_id
                except:
                    print i, "#ERR", sys.exc_info()
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table,
                context=context)

        # ---------------------------------------------------------------------
        # TODO pricelist
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # res.partner and res.partner.address
        # ---------------------------------------------------------------------
        table = 'res.partner'
        self._converter[table] = {}
        converter = self._converter[table] # for use same name
        if wiz_proxy.partner:
            # -----------------------------------------------------------------
            # A. Searching for partner (master):
            # -----------------------------------------------------------------
            item_pool = self.pool.get(table)
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
                            print i, "#INFO", table, "update:", item.name
                        else:
                            print i, "#INFO", table, "jumped:", item.name
                    else: # Create
                        item_id = item_pool.create(
                            cr, uid, data, context=context)
                        print i, "#INFO", table, "create:", item.name
                    converter[item.id] = item_id
                except:
                    print data
                    print i, "#ERR", table, "jump:", item.name, sys.exc_info()
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
                    partner_id = converter[item.id] # TODO test error
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
                            print "#INFO", table, "partner-addr upd:", item.partner_id.name
                    else: # Create
                        print "#ERR", table ,"partner-addr not found", item.partner_id.name
                    converter[item.id] = item_id

                except:
                    print "#ERR", table, "jumped:", item.partner_id.name
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
                            print "#INFO", table, "(dest) upd:", item.name
                        else:
                            print "#INFO", table, "(dest) jump:", item.name
                    else: # Create
                        item_id = item_pool.create(cr, uid, data,
                            context=context)
                        print "#INFO", table ,"(dest) create:", item.name
                    converter[item.id] = item_id

                except:
                    print "#ERR", table, "(dest) jumped:", item.name
                    continue
                # NOTE No contact for this database
        else: # Load convert list form database
            self.load_converter(cr, uid, converter, table=table,
                context=context)
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
