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

    # Extra button in wizard:
    def fast_migrate_country(self, cr, uid, context=None):
        ''' Module for fast append info:
        '''
        # ---------------------------------------------------------------------
        #      Common part: connection to old database using ERPEEK v. 6.0
        # ---------------------------------------------------------------------
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
        
        # ---------------------------------------------------------------------
        # res.country (name for get ID)
        # ---------------------------------------------------------------------
        obj = 'res.country'
        _logger.info("Start %s" % obj)
        self._converter[obj] = {}
        converter = self._converter[obj] # for use same name
        erp_pool = erp.ResCountry
        item_pool = self.pool.get(obj)
        item_ids = erp_pool.search([])
        for item in erp_pool.browse(item_ids):
            try:
                item_ids = item_pool.search(cr, uid, [('name', '=', item.name)]
                if item_ids
                    converter[item.id] = item_ids[0]
                else:
                    print "ERR name not found: %s" % item.name    
            except:
                print "#ERR", obj, "jumped:", item.name
                continue

        # ------------------------------------
        # Syncro partner with all informations
        # ------------------------------------
        obj = 'res.partner'
        _logger.info("Start %s" % obj)
        item_pool = self.pool.get(obj)
        erp_pool = erp.ResPartner # v. 6.0
        item_ids = erp_pool.search([]) 
        i = 0            
        for item in erp_pool.browse(item_ids):
            try:
                i += 1                
                if item.country_id:
                    country_id = self._converter['res.country'].get(item.country_id.id, False)
                    if country_id:
                        item_pool.write(cr, uid, { 
                            'country_id': country_id,
                            }, context=context)
                            
                    print i, "#INFO", obj, "update:", item.name
            except:
                print i, "#ERR", obj, "jump:", item.name, sys.exc_info()
                continue
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:class ResPartnerCategory(orm.Model):
