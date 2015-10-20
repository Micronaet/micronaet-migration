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

# Function:

def get_name(item):
    ''' Get name 3 field and delete code on the left
    '''
    res = ''
    name = item.k2_image_caption or item.description_sale or item.name or ''
    for c in name.split('] ')[-1]:
        if ord(c) < 128:
            res += c
        else:
            res += ''
    return res
    
# -----------------------------------------------------------------------------
#        Set up parameters (for connection to Open ERP Database) 
# -----------------------------------------------------------------------------

config = ConfigParser.ConfigParser()

config_file = os.path.expanduser('openerp.cfg')
config.read([config_file])

# Open connection with 6:
server6 = config.get('openerp6', 'server')
port6 = config.get('openerp6', 'port')
dbname6 = config.get('openerp6', 'dbname')
user6 = config.get('openerp6', 'user')
pwd6 = config.get('openerp6', 'pwd')
erp6 = erppeek.Client(
    'http://%s:%s' % (server6, port6),
    db=dbname6,
    user=user6,
    password=pwd6,
    )

# Open connection with 8:
server8 = config.get('openerp8', 'server')
port8 = config.get('openerp8', 'port')
dbname8 = config.get('openerp8', 'dbname')
user8 = config.get('openerp8', 'user')
pwd8 = config.get('openerp8', 'pwd')
#erp8 = erppeek.Client(
#    'http://%s:%s' % (server8, port8),
#    db=dbname8,
#    user=user8,
#    password=pwd8,
#    )

product_pool = erp6.ProductProduct
item_ids = product_pool.search([])

erp6.context = {'lang': 'it_IT'}
origin = {}
out_f = open('lista.csv', 'w')
for item in product_pool.browse(item_ids):
    origin[item.default_code] = [get_name(item), '']
    print 'Italiano:', item.default_code

erp6.context['lang'] = 'en_US'
out_f.write('Codice;Italiano;Inglese\n')
for item in product_pool.browse(item_ids):
    try:
        origin[item.default_code][1] = get_name(item)
        print 'Inglese:', item.default_code
    except:
        print 'Codice %s not found!' % item.default_code
        origin[item.default_code][1] = '#ERR'

    out_f.write('%s;%s;%s\n' % (
        item.default_code,
        origin[item.default_code][0],
        origin[item.default_code][1],
        ))
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
