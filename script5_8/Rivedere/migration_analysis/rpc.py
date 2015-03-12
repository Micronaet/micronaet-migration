#!/usr/bin/python
# -*- encoding: utf-8 -*-

import os
import sys
import xmlrpclib
import ConfigParser


# Set up parameters (for connection to Open ERP Database) **********************
config_file_6 = os.path.join(os.path.expanduser("~"), "etl", "minerals", "openerp.6.cfg")
config_6 = ConfigParser.ConfigParser()
config_6.read([config_file_6]) 
dbname_6 = config_6.get('dbaccess', 'dbname')
user_6 = config_6.get('dbaccess', 'user')
pwd_6 = config_6.get('dbaccess', 'pwd')
server_6 = config_6.get('dbaccess', 'server')
port_6 = config_6.get('dbaccess', 'port')

# For final user: Do not modify nothing below this line (Python Code) **********
sock_6 = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (server_6,  port_6))
uid_6 = sock_6.login(dbname_6, user_6 ,pwd_6)
sock_6 = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object' % (server_6, port_6))
sock_6.execute(dbname_6, uid_6, pwd_6, 'migration.tools', 'get_openerp_tree')
