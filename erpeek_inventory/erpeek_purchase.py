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
path = '~/ETL/GPB'
config_file = os.path.join(os.path.expanduser(path), 'openerp.cfg')
config = ConfigParser.ConfigParser()
config.read([config_file])

# Connection:
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')  
database = config.get('dbaccess','dbname')
user = config.get('dbaccess', 'user')
password = config.get('dbaccess', 'pwd') 

# File CSV
filename = os.path.expanduser(config.get('purchase', 'filename') )
delimiter = config.get('purchase', 'delimiter') 
header = eval(config.get('purchase', 'header'))

odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=database, 
    user=user, 
    password=password,
    )

product = odoo.model('product.product')
purchase = odoo.model('purchase.order')
purchase_line = odoo.model('purchase.order.line')

order = 'PO00357'
purchase_ids = purchase.search([('name', '=', order)])
if not purchase_ids:
    print 'Purchase', order, 'not found'
    sys.exit()
purchase_id = purchase_ids[0]

i = -header
for row in csv.reader(
        open(filename, 'rb'), delimiter=delimiter):
    try:    
        i += 1
        if i <= 0:
            continue # jump line
        default_code = row[0]
        inventory = float(row[4].replace(',', '.'))
        if not inventory:
            print "Quantity not found:", default_code, "quantity", inventory
            continue

        # Search product code:     
        product_ids = product.search([
            ('default_code', 'ilike', default_code)])

        if len(product_ids) > 1:
            print "More than one", default_code, len(product_ids), inventory
            continue
        elif not product_ids:     
            print "No product found:", default_code, "quantity", inventory
            continue
        
        product_proxy = product.browse(product_ids)[0]        
        data = {
            'name': product_proxy.name,
            'order_id': purchase_id,
            'product_id': product_ids[0],
            'product_qty': inventory,
            'price_unit': 1.0,
            'date_planned': '2015/08/05',            
            }

        line_ids = purchase_line.search([
            ('order_id', '=', purchase_id),
            ('product_id', '=', product_ids[0]),
            ])
        if line_ids:
            purchase_line.write(line_ids, data)
            print "Update:", default_code, "quantity", inventory
        else:
            purchase_line.create(data)
            print "Create:", default_code, "quantity", inventory

    except:
        print 'Unmanaged error:', default_code, inventory, sys.exc_info()

