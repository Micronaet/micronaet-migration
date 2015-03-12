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

class SyncroPartner(orm.Model):
    ''' Function for migration (and setup parameters for XMLRPC
    '''
    _name = 'syncro.partner'

    # -------------------------------------------------------------------------
    # Syncro / Migration procedures:   
    # -------------------------------------------------------------------------
    def syncro_partner(self, cr, uid, context=None):
        ''' Module for syncro partner from one DB to another
        '''
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
                
        partner_pool = self.pool.get('res.partner')      

        partner_ids = sock.execute(
            openerp.name, uid_old, openerp.password, 
            'res.partner', 'search', [])
        
        partner_transcode = {} # key = ID 7 : value = ID 8
        contact_partner_id = {} # Key = ID contact 8: value = ID 7 partner_id
        for partner in sock.execute(openerp.name, uid_old, openerp.password, 
                'res.partner', 'read', partner_ids):
            try:    
                data = { # TODO complete
                    'name': partner['name'],
                    #'comment': partner.comment,
                    #'ean13': partner.ean13,
                    #'street': partner.street,
                    #'city': partner.city,
                    #'supplier': partner.supplier,
                    #'ref': partner.ref,
                    #'email': partner.email,
                    #'website': partner.website,
                    #'customer': partner.customer,
                    #'is_company': partner.is_company,
                    #'fax': partner.fax,
                    #'street2': partner.street2,
                    #'active': partner.active,
                    #'phone': partner.phone,
                    #'mobile': partner.mobile,
                    #'fiscalcode': partner.fiscalcode,
                    #type
                    #'birthdate': partner.birthdate,
                    #'vat': partner.vat,
                    #'notify_email': partner.nofify_email,
                    #'opt_out': partner.opt_out,
                    #'is_address': partner.is_address,                
                    }
                
                new_ids = partner_pool.search(cr, uid, [
                    ('migration_old_id', '=', partner['id'])], context=context)
                if new_ids: # Modify
                    partner_id = new_ids[0]
                    partner_pool.write(cr, uid, partner_id, data, 
                        context=context)
                    print "#INFO Partner update:", partner['name']                   
                else: # Create
                    partner_id = partner_pool.create(cr, uid, data, 
                        context=context)                        
                    partner_pool.write(cr, uid, partner.id, {
                        'migration_old_id': partner_id, 
                        }, context=context)
                    print "#INFO Partner create:", partner['name']
                    
                # Save info for next write of partner_id    
                #if partner.is_address or not partner.is_company: # Add. Cont.
                #    # ID v.8 = parent_id v.7
                #    contact_code[partner_id] = partner.parent_id.id
                #else: # Partner (save transoce for id 7 > 8                                        
                #    # Current ID (v.7)            = Other ID (v.8)    
                #    partner_transcode[partner.id] = partner_id
                
            except:
                print "#ERR Partner jumped:", partner['name']
            #for contact in contact_code:
            #    sock.execute(
            #        openerp.name, uid_old, openerp.password, 
            #        'res.partner', 'write', 
            #        contact, {
            #            'parent_id': partner_transcode[contact_code[contact]]
            #           })
        return True
            
    _columns = {
        'name': fields.char('Source DB name', size=80, required=True),
        'hostname': fields.char('Source Hostname', size=80, required=True),
        'port': fields.integer('Source Port', required=True),
        'username': fields.char('Source Username', size=80, required=True),
        'password': fields.char('Source Password', size=80, required=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

