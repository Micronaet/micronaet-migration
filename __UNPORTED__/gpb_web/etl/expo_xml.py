#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules used for ETL customers/suppliers
# use: ETL.py file_csv_to_import

# Modules required:
import ConfigParser, xmlrpclib


# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.gpb.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test


# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

import pdb; pdb.set_trace()
f = open('prodotti.xml', 'w')
f.write('    <prodotti>\n')
product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('in_pricelist', '=', True)])
for prodotto in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids):
    f.write('    <prodotto>\n')
    f.write('       <code>%s</code>\n'%(prodotto['code']))
    f.write('       <name>%s</name>\n'%(prodotto['name']))
    f.write('       <ean13>%s</ean13>\n'%(prodotto['ean13']))
    f.write('       <description>%s</description>\n'%(prodotto['description']))
    f.write('       <description_web>%s</description_web>\n'%(prodotto['description_web']))
    f.write('       <colour>%s</colour>\n'%(prodotto['colour']))
    f.write('       <type_of_material>%s</type_of_material>\n'%(prodotto['type_of_material']))
    f.write('       <uom_id>%s</uom_id>\n'%(prodotto['uom_id']))
    f.write('       <q_x_pack>%s</q_x_pack>\n'%(prodotto['q_x_pack']))
    f.write('       <length>%s</length>\n'%(prodotto['length']))
    f.write('       <height>%s</height>\n'%(prodotto['height']))
    f.write('       <width>%s</width>\n'%(prodotto['width']))
    f.write('       <weight>%s</weight>\n'%(prodotto['weight']))
    f.write('       <weight_net>%s</weight_net>\n'%(prodotto['weight_net']))
    f.write('       <volume>%s</volume>\n'%(prodotto['volume']))
    f.write('       <fabric>%s</fabric>\n'%(prodotto['fabric']))
    f.write('       <list_price>%s</list_price>\n'%(prodotto['list_price']))
    f.write('    </prodotto>\n')
f.write('    </prodotti>\n')

