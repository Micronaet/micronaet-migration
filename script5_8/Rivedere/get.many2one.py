#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
import sys, os
from openerp import migration
from openerp.utility import *


# ------------------------------------------------------------------------------
#                        Pre import analysis (documentation)
# ------------------------------------------------------------------------------

# Tables v. 70:
openerp70 = migration.migration("Minerals70", "openerp", "30mcrt983")
tables_v70 = openerp70.tables_count()

if len(sys.argv)<2:
    print "Use: ./get.many2one.py 70 account_account"    
    print "Use: ./get.many2one.py 70    # All tables"
    sys.exit()
    
openerp = migration.migration("Minerals%s"%(sys.argv[1]) , "openerp", "30mcrt983")

if len(sys.argv)==3:    
    tables = [sys.argv[2].replace("_",".")]
else:
    tables = openerp.tables()

simple_tables = []    
for table in tables:
    m2o_list = openerp.many2one(table.replace("_","."))    
    
    if not m2o_list.keys():
        simple_tables.append(table)

    for key in m2o_list.keys():
        print "\n", "*"*80, "\n", "*", key , "*\n", "*"*80
        for col in m2o_list[key]:
            print "%-40s: %-40s >>> %-40s"%(table, col, m2o_list[key][col])

print "\n\n", "*"*10, "\nAnagrafiche semplici: ", simple_tables
del openerp
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
