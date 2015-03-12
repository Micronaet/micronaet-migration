#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
import psycopg2 
import sys, os

from openerp import migration
from openerp.utility import *

file_name = os.path.join(".", "variables.py")
dict_file = open(file_name, "w") # File where is saved the dictionary

table_migration = {}

# Tables v. 60:
openerp60 = migration.migration("Minerals60", "openerp", "30mcrt983")
tables_60 = openerp60.tables_count()
t60 = tables_60.keys()
t60.sort()

# Tables v. 70:
openerp70 = migration.migration("Minerals70", "openerp", "30mcrt983")
t70 = openerp70.tables()

# -------------
# table only 60            
# -------------
for table in t60:   
    if table in t70:            
        from_column = openerp60.get_column_list(table)
        to_column   = openerp70.get_column_list(table)
        
        table_migration[table] = [
                                  tables_60[table] > 0,                                          # 0. To migrate
                                  False,                                                         # 1. Erase destination
                                  False,                                                         # 2. Field for sincronization (es. 'code') is for integration
                                  [column for column in from_column],                            # 3. Field 6
                                  [column for column in from_column if column not in to_column], # 4. Field 6 not in 7
                                  [column for column in from_column if column in to_column],     # 5. Field 6 = 7
                                  [column for column in to_column],                              # 6. Field 7
                                  [column for column in to_column if column not in from_column], # 7. Field 7 not in 6
                                  {},                                                            # 8. Mapping fields {'field_name_6': 'field_name_7'}
                                 ]
del openerp70, openerp60

# 1. esporto la lista delle tabelle
dict_file.write("#!/usr/bin/python\n# -*- coding: utf-8 -*-\n# To migrate, Erase destination, Sync field, [Field6], [Field6not7], [Field6and7], [Field7],[Field7not6], Mapping\ntable_migration = {\n") # Header
write_all_dict(dict_file, table_migration)                                     # Dict elements
dict_file.write("}\n")                                                         # Bottom 

# 2. lascio modificare con s o n se devo fare la migrazione 
print "Import file created, modify dict in it! (%s)"%(file_name,)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
