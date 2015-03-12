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
''' Importation note:
    No importation, create only conversion Database and put manually old new ID
'''

import sys, os
from database.berkeley import conversion


def migrate(o6, o7, berkeley_tables):
    ''' Migrate object
    '''
    obj = "res.company"
    table = obj.replace(".", "_")
    
    if obj not in berkeley_tables:
        berkeley_tables[obj] = conversion(o6._dbname, obj)

    # Migrate one by one all record:
    
    # Adjust creation standard 4 fields:
    
    # Save conversion ID:
    berkeley_tables[obj].write(1, 1) # Minerals

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
