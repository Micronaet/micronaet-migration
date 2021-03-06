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

class SyncroMigrationWizard(orm.TransientModel):    
    ''' Wizard for migrate
    '''
    
    _name = "syncro.migration.account.wizard"

    # Fast procedure:
    def fast_migrate_country(self, cr, uid, ids, context=None):
        return self.pool.get('syncro.xmlrpc'). fast_migrate_country(
            cr, uid, context=context)
            
    # Wizard button:
    def migrate_database(self, cr, uid, ids, context=None):  
        self.pool.get('syncro.xmlrpc.account').migrate_database(
            cr, uid, 
            self.browse(cr, uid, ids, context=context)[0], # proxy for param.
            context=context)
        return {}

    _columns = {
        'from_date': fields.datetime('From date'),
        'to_date': fields.datetime('To date'),

        'to_create': fields.boolean('Create if not present'),
        'update': fields.boolean('Update if present'),

        'user': fields.boolean('A. User > Product > Employee'),
        'product': fields.boolean('B. Product > Account analytic'),
        'partner': fields.boolean('D. Account analytic > Partner'),
        'line': fields.boolean('E. Account analytic line'),
        }
        
    _defaults = {
        'create': lambda *x: False,
        'update': lambda *x: False,
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
