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
from openerp.openerp import server
from analysis.tree import nodes


# -----------------------------------------------------------------------------
#        Set up parameters (for connection to Open ERP Database) 
# -----------------------------------------------------------------------------
config = ConfigParser.ConfigParser()

config_file = os.path.expanduser(
    os.path.join("~", "etl", "GFC", "openerp.5.cfg"))
config.read([config_file])
host5 = config.get('dbaccess', 'server')
dbname5 = config.get('dbaccess', 'dbname')
orm_user5 = config.get('dbaccess', 'user')
orm_pwd5 = config.get('dbaccess', 'pwd')
orm_port5 = config.get('dbaccess', 'port')
pg_user5 = config.get('postgres', 'user')
pg_pwd5 = config.get('postgres', 'pwd')
pg_port5 = config.get('postgres', 'port')
verbose5 = config.get('import_mode', 'verbose')

# Tables v. 50:
05 = server(
    dbname=dbname5, host=host5, verbose=verbose5,
    orm_user=orm_user5, orm_password=orm_pwd5, orm_port=orm_port5,
    pg_user=pg_user5, pg_password=pg_pwd5, pg_port=pg_port5)

# -----------------------------------------------------------------------------
#                              Tree node analysis:
# -----------------------------------------------------------------------------
nl = nodes(05)

if len(sys.argv) == 1:          # no range (all tree first level)
    nl.info()
elif len(sys.argv) == 2:        # tree of a object
    name = sys.argv[1]
    nl.draw_tree(name, only_field = 'many2one')
    #nl.draw_tree(name, only_filed = 'many2many')
elif len(sys.argv) == 3:        # range (only selected range level)
    nl.info(score_range = (int(sys.argv[1]), int(sys.argv[2])))
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
