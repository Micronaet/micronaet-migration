#!/usr/bin/python
# -*- encoding: utf-8 -*-

import os
import sys
import xmlrpclib
import ConfigParser


# Set up parameters (for connection to Open ERP Database) **********************
config_file_7 = os.path.join(os.path.expanduser("~"), "etl", "minerals", "openerp.7.cfg")
config_7 = ConfigParser.ConfigParser()
config_7.read([config_file_7]) 
dbname_7 = config_7.get('dbaccess', 'dbname')
user_7 = config_7.get('dbaccess', 'user')
pwd_7 = config_7.get('dbaccess', 'pwd')
server_7 = config_7.get('dbaccess', 'server')
port_7 = config_7.get('dbaccess', 'port')

# For final user: Do not modify nothing below this line (Python Code) **********
sock_7 = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (server_7,  port_7))
uid_7 = sock_7.login(dbname_7, user_7 ,pwd_7)
sock_7 = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (server_7, port_7))

tabella = 'product.product'

tabella_id = sock_7.execute(dbname_7, uid_7, pwd_7, tabella, 'search', [('id', '<', 10)]) 
tabella_campi = sock_7.execute(dbname_7, uid_7, pwd_7, tabella, 'read', tabella_id)

import pdb; pdb.set_trace()
# 1. Creo tutto il record campi scalari e many2one (prima creo tutte le tabelle collegate)
# 2. Salvo il dato nel convertitore
# 3. Uso il convertitore per aggiornare da riga di comando i 4 campi extra non visibili (create_date e uid ecc.)
# Problemi: verificare propietà

item_id = sock_7.execute(dbname_7, uid_7, pwd_7, tabella, 'create', {'name': 'ciao', 'property_stock_production': 7})
item_id = sock_7.execute(dbname_7, uid_7, pwd_7, tabella, 'create', {'name': 'miao', 'property_stock_production': 7})
