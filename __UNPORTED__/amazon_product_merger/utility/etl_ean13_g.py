#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Create EAN code for all GPB product
# Modules required:
import xmlrpclib, sys, ConfigParser, os
import math

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([os.path.expanduser("~/ETL/gpb/openerp.cfg")])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

def get_checksum_ean(eancode12):
    ''' Generate checksum char for 12 char EAN passed
    '''
    
    '''if not eancode12 or len(eancode12) <> 12:
        return False
    try:
        int(eancode12)
    except:
        return False'''

    oddsum = evensum = total=0
    reverseean=eancode12[::-1]

    for i in range(len(reverseean)):
        if i%2:
            evensum += int(reverseean[i])
        else:
            oddsum += int(reverseean[i])
    total = (oddsum * 3) + evensum

    check = int(10 - math.ceil(total % 10.0)) %10
    return check
    

product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('ean13', '=', False)])

for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ('id', 'default_code',)):
    code = product['default_code']
    try:
        test = int(code) # for raise error!
        if len(code)==5:
            ean12 = "8004467%s"%(code,)
            ean13 = "%s%s"%(ean12, get_checksum_ean(ean12))
            sock.execute(dbname, uid, pwd, 'product.product', 'write', product['id'], {'ean13': ean13,})
            print "UPDATED: %s EAN13:%s"%(code, ean13)
    except:
        print "ERROR: %s "%(code,)

