# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import csv
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
#                              Objects:
# -----------------------------------------------------------------------------
class ResPartnerGroup(orm.Model):
    """ Partner group for statistic purpose
    """
    _name = 'res.partner.group'
    _description = 'Partner group'
    _order = 'name'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'note': fields.text('Note'),
        }

class ResPartner(orm.Model):
    """ Partner group for statistic purpose
    """
    _inherit = 'res.partner'

    _columns = {
        'partner_group_id': fields.many2one('res.partner.group', 
            'Partner group'),
        }

class ResPartnerGroup(orm.Model):
    """ Partner group for statistic purpose
    """
    _inherit = 'res.partner.group'

    _columns = {
        'partner_ids': fields.one2many('res.partner.group', 
            'partner_group_id', 'Partners')
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
