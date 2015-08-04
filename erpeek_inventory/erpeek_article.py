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

import sys
import os
import csv
import erppeek
import ConfigParser

# Set up parameters (for connection to Open ERP Database) *********************
config_file = os.path.expanduser('~/ETL/GPB/openerp.cfg')
config = ConfigParser.ConfigParser()
config.read([config_file])

# Connection:
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')  
database = config.get('dbaccess','dbname')
user = config.get('dbaccess', 'user')
password = config.get('dbaccess', 'pwd') 

# File CSV
filename = config.get('csv', 'filename') 
delimiter = config.get('csv', 'delimiter') 
header = config.get('csv', 'header') 

odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=database, 
    user=user, 
    password=password,
    )

product = odoo.model('product.product')

i = -header
for row in csv.reader(
        open(filename, 'rb'), delimiter=delimiter):
    i += 1
    if i <= 0:
        print "# INFO Jump header line (%)" % header
    default_code = row[1]
    ean13 = row[2]
    
    product_ids = product.search([('default_code', '=', default_code)])
    if product_ids:
        product.write(product_ids, {
           'ean13': ean13,
            })
        print "# INFO Code: % updated with EAN13: %s" % (default_code, ean13)
    else:        
        print "# ERR  Code: % updated with EAN13: %s" % (default_code, ean13)

