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

# ---------------
# Utility method:
# ---------------

def list_to_string(list_to_convert):
    ''' Convert a list to a string wit space separation
    '''
    return ("%s"%(list_to_convert)).replace("[","").replace("]","").replace(",","")#.replace(")","").replace("(","")

def write_all_dict(dict_file, table_migration):
    ''' Write, well formatted a dict on a file (not in all one line)
    '''
    key_list = table_migration.keys()
    key_list.sort()
    for key in key_list:
        dict_file.write("\t'%s': %s,\n"%(key, 
                                       table_migration[key],
                                       ))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
