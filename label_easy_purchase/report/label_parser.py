#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2010-2012 Associazione OpenERP Italia
#   (<http://www.openerp-italia.org>).
#   Copyright(c)2008-2010 SIA "KN dati".(http://kndati.lv) All Rights Reserved.
#                   General contacts <info@kndati.lv>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_objects': self.get_objects,
            'get_ean': self.get_ean,
            })

    def get_ean(self, line, verbose=True):
        """ Explode label for purchase order
        """
        product = line.product_id
        if product:
            _logger.warning('>> Printing %s EAN %s' % (
                product.default_code,
                product.ean13,
            ))
        return line.product_id.ean13

    def get_objects(self, o):
        """ Explode label for purchase order
        """
        res = []
        for line in o.order_line:

            # Get Pz value:
            if line.product_id.q_x_pack >= 1:
                pz = int(line.product_id.q_x_pack)
            else:
                pz = 1

            # Force total depend on q x pack:
            total = int(line.product_qty)
            if pz > 1:
                total = int(total / pz) + (0 if total % pz == 0 else 1)

            for i in range(0, total):
                # Get part number if present:
                if line.product_id.force_coll:
                    colls = line.product_id.force_coll
                else:
                    try:
                        colls = float(line.product_id.colls.replace(',', '.'))
                    except:
                        colls = 1.0
                if colls and colls < 1:
                    parts = int(round(1 / colls, 0))
                else:
                    parts = 1

                # Multiply part number label:
                for part in range(1, parts + 1):
                    part_no = '%s / %s' % (part, parts)
                    res.append((part_no, pz, line))
        return res
