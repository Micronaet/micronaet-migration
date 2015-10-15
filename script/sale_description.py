#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
#    Micronaet S.r.l., Migration script for PostgreSQL
#    Copyright (C) 2002-2013 Micronaet SRL (<http://www.micronaet.it>). 
#    All Rights Reserved
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
import ConfigParser
import erppeek

# -----------------------------------------------------------------------------
#        Set up parameters (for connection to Open ERP Database) 
# -----------------------------------------------------------------------------
config = ConfigParser.ConfigParser()

config_file = os.path.expanduser('openerp.cfg')
config.read([config_file])

# Open connection with 5:
server5 = config.get('openerp5', 'server')
port5 = config.get('openerp5', 'port')
dbname5 = config.get('openerp5', 'dbname')
user5 = config.get('openerp5', 'user')
pwd5 = config.get('openerp5', 'pwd')
erp5 = erppeek.Client(
    'http://%s:%s' % (server5, port5),
    db=dbname5,
    user=user5,
    password=pwd5,
    )

# Open connection with 8:
server8 = config.get('openerp8', 'server')
port8 = config.get('openerp8', 'port')
dbname8 = config.get('openerp8', 'dbname')
user8 = config.get('openerp8', 'user')
pwd8 = config.get('openerp8', 'pwd')
erp8 = erppeek.Client(
    'http://%s:%s' % (server8, port8),
    db=dbname8,
    user=user8,
    password=pwd8,
    )

product_pool = erp.ProductProduct
item_ids = product_pool.search([])
for item in erp_pool.browse(item_ids, {'lang': 'it_IT'}):
    print item.description_sale

for item in erp_pool.browse(item_ids, {'lang': 'en_US'}):
    print item.description_sale
    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
