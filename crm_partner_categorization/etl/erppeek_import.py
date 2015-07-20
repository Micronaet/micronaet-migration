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

import erppeek
import ConfigParser

# -----------------------------------------------------------------------------
#                             Read Parameters:
# -----------------------------------------------------------------------------
cfg_file = "odoo.cfg" # same directory
config = ConfigParser.ConfigParser()
config.read(cfg_file)

# General parameters:
server = config.get('odoo', 'server')
port = eval(config.get('odoo', 'port'))
database = config.get('odoo', 'database')
user = config.get('odoo', 'user')
password = config.get('odoo', 'password')

file_in = config.get('csv', 'name')
separator = eval(config.get('csv', 'separator'))
header =  eval(config.get('csv', 'header'))

# -----------------------------------------------------------------------------
#                               Start procedure:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (server, port), 
    db=database, 
    user=user, 
    password=password
    )

# Pool used:
product_pool = odoo.model('product.product')
category_pool = odoo.model('product.category')
tipology_pool = odoo.model('product.tipology')
line_pool = odoo.model('product.line')
material_pool = odoo.model('product.material')

# ----------------------------------
# Read element needed for conversion
# ----------------------------------
tipology_ids = tipology_pool.search([])
tipology_convert = {}
if tipology_ids:
    for item in tipology_pool.browse(family_ids):
        tipology_convert[item.name] = [item.id, []] 

category_ids = category_pool.search([])
category_convert = {}
if category_ids:
    for item in category_pool.browse(category_ids):
        category_convert[item.name] = [item.id, []] 

# -------------------------
# Load elements from files:
# -------------------------
i = -header
max_col = False
for row in open(file_in, 'rb'):
    line = row.split(separator)
    i += 1
    if i <= 0: # jump header
        continue
    if not max_col:
        max_col = len(line)    
    default_code = line[0]
    tipology = line[1]
    category = line[2]
    
    # -------------------------------------
    # Check in converter, elsewhere create:
    # -------------------------------------
    if tipology not in tipology_convert:        
        # Create dict record 
        tipology_convert[tipology] = [
            tipology_pool.create({
                'name': tipology,
                })]   
    
    if category not in category_convert:        
        # Create dict record 
        category_convert[tipology] = [
            category_pool.create({
                'name': category,
                })]   
    
    # -------------------------------------
    # Check product 
    # -------------------------------------
    product_ids = product_pool.search([('default_code', '=', default_code)])
    if product_ids:
        if len(product_ids) > 1:
            print "More than one instance: %s (%s)" % (
                default_code, len(product_ids)
                )
        product_pool.write(product_ids[0], {
            'tipology_id': tipology_convert[tipology],
            'category_id': category_convert[category],
            })

