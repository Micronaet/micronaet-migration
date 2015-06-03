#!/usr/bin/env python
# -*- encoding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


import os
import sys
import xmlrpclib
import csv
import ConfigParser

path = os.path.expanduser(os.path.join('~', 'etl', 'purchase'))
filename = os.path.join(path, 'product.csv')

# -----------------------------------------------------------------------------
# Function:
# -----------------------------------------------------------------------------
def clean(valore):
    res = ""
    for c in valore:
        if ord(c) >= 128:
            res += "#"
        else: 
            res += c    
        
    return res    

def format_string(valore):
    valore = valore.decode('cp1252')
    valore = valore.encode('utf-8')
    return valore.strip()

def format_date(valore):
    if valore: # TODO test correct date format
       return valore
    else:
       return time.strftime("%d/%m/%Y")

def format_float(valore):
    valore = valore.strip().upper()
    valore = valore.replace("CM.", "").replace("CM", "")
    valore = valore.split(" ")[-1]
    try:
        if valore: # TODO test correct date format       
           return float(valore.replace(",","."))
        else:
           return 0.0   # for empty values
    except:
        print "Error conversion:", sys.exc_info()
        return 0.0       

# -----------------------------------------------------------------------------
# Start main code 
# -----------------------------------------------------------------------------
cfg_file = os.path.join(path, 'openerp.cfg')
   
# Set up parameters (for connection to Open ERP Database)
config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint
separator = config.get('dbaccess', 'separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname, user, pwd)
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

#lines = csv.reader(open(filename, 'rb'), delimiter=separator)
lines = open(filename, 'rb')

i = 0
for row in lines:
    row = clean(row)
    line = row.strip().split(separator)
    i += 1 
    if not len(line) or len(line) != 21: # jump empty lines
        print "Line jumped"
        continue
    default_code = format_string(line[0]) ##
    supplier = format_string(line[1]) #
    name = format_string(line[2]) ##
    description = format_string(line[3]) ## 
    campaign_qty = format_string(line[4]) 
    reserve = format_string(line[5]) 
    price_supplier = format_float(line[6]) #
    colour = format_string(line[7]) ##
    colour_code = format_string(line[8]) ##
    L = format_float(line[9])
    H = format_float(line[10])
    D = format_float(line[11])
    diameter = format_float(line[12])
    H_sit = format_float(line[13])
    comment = format_string(line[14])
    weight = format_float(line[15]) #
    L_pack = format_float(line[16]) ##
    H_pack = format_float(line[17]) ##
    D_pack = format_float(line[18]) ##
    colls = format_string(line[19]) ##
    ean13 = format_string(line[20]) ##
   
    data = {
        'default_code': default_code,
        'code': default_code,
        #name,
        #description,
        #campaign_qty,
        #price_supplier,
        #material,
        'standard_price': price_supplier,
        'colour': colour,
        'colour_code': colour_code,        
        'width': L,
        'height': H,
        'length': D,
        'pack_l': L_pack,
        'pack_h': H_pack,
        'pack_p': D_pack,
        
        'default_supplier': supplier,
        #'description_purchase': ,
        #'default_supplier_name': supplier,
        #'default_supplier_code': supplier,
        #diameter,
        #H_sit,
        #comment,
        'weight': weight,
        #mounted,
        #L1,
        #H1,
        #D1,
        #weight1,
        'colls': colls,
        'ean13': ean13,
        }
    product_ids = sock.execute( # search current ref
        dbname, uid, pwd, 'product.product', 'search', [
            ('default_code', '=', default_code),])                       
       
    if product_ids:
        try:
            sock.execute( # search current ref
                dbname, uid, pwd, 'product.product', 'write', 
                product_ids, data)                   
        except:
            print "Riga", i, "Error:", row#, data
            continue        
    else:
        print "Riga", i, "Code not found", default_code
        #product_id = sock.execute(
        #    dbname, uid, pwd, 'product.product', 'create', data)                   
    print "Riga", i
    #except: 
    #    print "Errore importando, record saltato", sys.exc_info()    
    #    continue
