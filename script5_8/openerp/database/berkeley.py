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
import bsddb


# -----------------------------------------------------------------------------
#                                   CLASS
# -----------------------------------------------------------------------------

class berkeley():
    ''' Class for manage OpenERP server (both: ORM, XMLRPC)
    '''
    # -------------------------------------------------------------------------
    #                            Private data
    # -------------------------------------------------------------------------
    _db = False         # Database handle
    _database = False   # Database name
    _table = False      # Database table / object (format "openerp.object.name")
    
    # -------------------------------------------------------------------------
    #                            Magic method
    # -------------------------------------------------------------------------
    def __init__(self, database, table, default_path = ("~", "openerpdb"), force_reset = False):
        ''' Conversion database elements

            self: object reference
            database: name of database (used also in file name)
            table: table name (used also in file name)
            default_path: list or tuple with default folder where DB file are
        '''

        path = os.path.expanduser(os.path.join(*default_path))
        self._table = table
        self._database = database

        try:
            os.mkdir(path)
        except:
            pass # if yet exist

        path = os.path.join(path, database)
        try:
            os.mkdir(path)
        except:
            pass # if yet exist
        
        file_name = os.path.join(path, '%s.db' % (table, ))
        if force_reset:
            try:
                os.remove(file_name)
            except:
                pass # if not present no error    
        self._db = bsddb.btopen(file_name, 'c')

    # -------------------------------------------------------------------------
    #                             Public method
    # -------------------------------------------------------------------------
    def show(self, ):
        ''' Show all records
        
            self: object reference
        '''
        print "=" * 27
        print "| Old V.6 | New V.7 | Mod |"
        print "=" * 27
        for k, v in self._db.iteritems():
        
            print "| %7s | %7s | %3s |" % (k, v, "***" if k != v else "")
        print "=" * 27
        return
        
    def write(self, key, value):
        ''' Create DB record with key value passed:
        
            self: object reference
            key: old ID
            value: new ID
        '''
        self._db["%d" % key] = "%d" % value

    def read(self, key):
        ''' Read DB record:

            self: object reference
            key: old ID
            @return: new ID
        '''
        try:
            return int(self._db["%d" % key])
        except:
            return False
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
