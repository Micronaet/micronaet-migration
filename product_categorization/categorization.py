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

class ProductLine(orm.Model):
    ''' Every product have an associated category 
    '''    
    _name = 'product.line'
    _description = 'Product line'
    _order = "name"
        
    _columns = {
        'name': fields.char('Line', size=80, required=True, translate=True),
        'note': fields.text('Note'),
        # TODO depend on category
        #'category_id': fields.many2one('web.category', 'Category', 
        #required=True),
        }

class ProductTipology(orm.Model):
    ''' Every product have an associated tipology
    '''    
    _name = 'product.tipology'
    _description = 'Product tipology'
    _order = "name"

    _columns = {
        'name': fields.char('tipology', size=80, required=True, readonly=False,
             translate=True),
        'note': fields.text('Note'),
    }

class ProductMaterial(orm.Model):
    ''' Every product have an associated material
    '''    
    _name = 'product.material'
    _description = 'Product material'
    _order = 'name'

    _columns = {
        'name': fields.char('Material', size=80, required=True, readonly=False,
             translate=True),
        'note': fields.text('Note'),
    }
#class ProductSubtipology(orm.Model):
#    ''' Every product have an associated subtipology
#    '''
#    
#    _name = 'product.subtipology'
#    _description = 'Product subtipology'
#
#    _columns = {
#        'name': fields.char('Subtipology', size=80, required=True, 
#            translate=True),
#        'tipology_id': fields.many2one('web.tipology', 'Tipology'),
#    }


#class web_tipology(osv.osv):
#    ''' Extra relation fields for tipology
#    '''    
#    _name = 'web.tipology'
#    _inherit = 'web.tipology'
#
#    _columns = {
#        'subtipology_ids':fields.one2many('web.subtipology', 'tipology_id', 
#        'Subtipology', required=False),
#    }

class ProductProduct(orm.Model):
    _inherit ='product.product'

    _columns = {
        #'category_id': fields.many2one('web.category', 'Category', required=False),
        'line_id':fields.many2one('product.line', 'Line'),
        'tipology_id': fields.many2one('product.tipology', 'Tipology'),
        #'subtipology_ids': fields.many2many(
        #    'product.subtipology', 'product_subtipology_rel', 'product_id',
        #'subtipoloy_id','Subtipology'),
        
    }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
