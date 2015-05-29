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

class CrmPartnerImportance(orm.Model):
    _name = 'crm.partner.importance'
    _description = 'Partner importance'
    _order = 'sequence'

    _columns = {
        'name': fields.char('Name', size=10, required=True,
            help='ex.: **** or xxxx'),
        'symbol_description': fields.char(
            'Symbol description', size=64, required=False, readonly=False),
        'sequence': fields.integer(
            'Sequence', help='Order of importance level'),
        'note': fields.text(
            'Note', help='Some information to this level behaviours'),
        'invoiced_less_than': fields.float(
            'Invoice less than', digits=(16, 2)),
        'invoiced_over_than': fields.float(
            'Invoice over than', digits=(16, 2)),
        }

class ResPartnerExtraFields(orm.Model):
    _inherit = 'res.partner'

    def _get_last_activity(self, cr, uid, ids, args, field_list, context=None):
        '''
        Get last activity date:
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: list of dictionary which contain partner id, colour
        '''
        if context is None:
           context = {}

        res = dict.fromkeys(ids, 'no contacts')
        return res

    _columns = {
        'partner_color': fields.selection([
            ('green','Green'),
            ('yellow','Yellow'),
            ('red','Red'),
            ],'Color classification', select=True),
        'partner_importance_id':fields.many2one(
            'crm.partner.importance', 'Importance'),
        'last_activity': fields.function(
            _get_last_activity, method=True, type='char', size=30,
            string='Last activity', store=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
