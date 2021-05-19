#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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
import time
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


class EtlLogImportation(orm.Model):
    ''' Importation log element
    ''' 
    _name = 'etl.log.importation'
    _description = 'ETL Importation log'
    _order = 'datetime desc'

    def etl_log_event(self, cr, uid, name, filename, note, error, 
            context=None):
        """ Log ETL data
        """
        date_file = 'Data file: %s' % time.ctime(
            os.path.getctime(file_input1))
        log_ids = self.search(cr, uid, [
            ('name', '=', name),
            ], context=context)
        data = {
            'name': name,
            'note': note,
            'error': error,
            'date_file': date_file,
        } 
        if log_ids:
            self.create(cr, uid, data, context=context)
        else:    
            self.write(cr, uid, log_ids, data, context=context)

    _columns = {
        'name': fields.char('Sorgente ETL', size=90),
        'datetime': fields.datetime('Data creazione'),
        'date_file': fields.char('Data file', size=90),
        'note': fields.char('Note'),
        'error': fields.char('Error'),
        
        # File information:
        'filename': fields.char('Filename', size=80),
        }

    _defaults = {
        'datetime': lambda *x: datetime.now().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT),
        }
