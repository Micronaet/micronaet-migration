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

class EasyLabelPurchaseWizard(orm.TransientModel):
    '''Wizard for export the list of label to be lauched on Easy Label PC
    '''
    _name = 'easylabel.purchase.wizard'

    # -------------
    # Event button:
    # -------------
    
    def export_label(self, cr, uid, ids, context=None):
        ''' This event generate the batch command to be launched from Easy
            label PC, after generate the command to print all the label in 
            correct order.
            After this the label employee have to launch the link on his 
            destktop PC 
        '''
        return True
        
    _columns = {
        'note': fields.text('Note', help='Note for label employee'),
        'label_id': fields.many2one('easylabel.label', 'Label', required=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
