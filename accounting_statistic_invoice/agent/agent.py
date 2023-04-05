# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib
import ConfigParser

cfg_file = 'openerp.cfg'

# Set up parameters (for connection to Open ERP Database) *********************
config = ConfigParser.ConfigParser()
config.read([cfg_file])
# if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])

# DB access:
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

# CSV parameter:
file_partner = config.get('csv', 'partner')
file_product = config.get('csv', 'product')
parent_max = int(config.get('csv', 'parent'), 0)
delimiter = config.get('csv', 'delimiter')

# XMLRPC connection for authentication (UID) and proxy
sock = xmlrpclib.ServerProxy(
   'http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname, user, pwd)

sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

update = sock.execute(
    dbname, uid, pwd, 'statistic.invoice',
    'append_csv_statistic_delivery_data', file_partner, file_product,
    parent_max, delimiter)
