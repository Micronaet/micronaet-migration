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
data_path = os.path.expanduser("~/ETL/Migration")

# Tables v. 60:
openerp60 = migration.migration("Minerals60", "openerp", "30mcrt983")
tables_v60 = openerp60.tables_count()

# Tables v. 70:
openerp70 = migration.migration("Minerals70", "openerp", "30mcrt983")
tables_v70 = openerp70.tables_count()

file_table = open(os.path.join(data_path, "table.csv"), "w")            # List of table
file_table_data = open(os.path.join(data_path, "table_data.csv"), "w")  # List of table and extra data

# Header:
file_table.write("%s,%s,%s,%s,%s,%s,%s,%s\r\n"%("Table","Tot 60", "Tot 70", "Status", "col. 60 only", "col. 70 only", "column 60", "column 70"))
file_table_data.write("%s,%s,%s,%s,%s,%s,%s,%s\r\n"%("Table","Tot 60", "Tot 70", "Status", "col. 60 only", "col. 70 only", "column 60", "column 70"))

t60 = tables_v60.keys()
t60.sort()

t70=tables_v70.keys()
t70.sort()

# -------------
# table only 60            
# -------------
for table in t60:   
    if table not in tables_v70:        
        from_column = openerp60.get_column_list(table)
        record = "%s,%s,%s,%s,%s,%s,%s,%s\r\n"%(table, 
                                                tables_v60[table], 
                                                "", 
                                                "V60", 
                                                "", 
                                                "", 
                                                list_to_string(from_column),
                                                "",
                                               )
        file_table.write(record)
        if tables_v60[table]:
            file_table_data.write(record)
            
# -----------------            
# table all version            
# -----------------            
for table in t60:             # All 60 tables
    if table in tables_v70:   # If 60 is in 70 tables
        # ----------------------------    
        # Verifica situazione colonne:
        # ----------------------------    
        from_column = openerp60.get_column_list(table)
        to_column = openerp70.get_column_list(table)
        
        # Colonne che mancano  (60 si, 70 no):
        # Colonne nuove        (60 no, 70 si): 
        file_table.write("%s,%s,%s,%s,%s,%s,%s,%s\r\n"%(table, 
                                                  tables_v60[table],
                                                  tables_v70[table], 
                                                  "ALL", 
                                                  "", 
                                                  "",
                                                  "", 
                                                  "",
                                                  ))
                                                  
        if tables_v60[table]:
            file_table_data.write("%s,%s,%s,%s,%s,%s,%s,%s\r\n"%(table, 
                                                           tables_v60[table], 
                                                           tables_v70[table], 
                                                           "ALL", 
                                                           list_to_string([column for column in from_column if column not in to_column]), 
                                                           list_to_string([column for column in to_column if column not in from_column]),
                                                           list_to_string(from_column), 
                                                           list_to_string(to_column), 
                                                           ))
# -------------
# table only 70            
# -------------
for table in t70:  
    if table not in tables_v60:
        to_column = openerp70.get_column_list(table)
        record = "%s,%s,%s,%s,%s,%s,%s,%s\r\n"%(table, 
                                                "", 
                                                tables_v70[table], 
                                                "V70",
                                                "",
                                                "",
                                                "",
                                                list_to_string(to_column),
                                                )
                                                
        file_table.write(record)
        if tables_v70[table]:
            file_table_data.write(record)

del openerp70, openerp60

print "\n", "*"*50
print "Document created:\n%s\n%s"%(os.path.join(data_path, "table.csv"),
                                   os.path.join(data_path, "table_data.csv")) 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
