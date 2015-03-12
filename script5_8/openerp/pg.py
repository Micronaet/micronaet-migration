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

# ---------------
# Class:
# ---------------

def pg_datetime(value):
    ''' Return PG date from datetime elements passed
    '''
    res = 'null'
    try:
        if value:
            return "'%s'" % (value.strftime("%Y-%m-%d %H:%M:%S.%f"),)
    except:
        pass
    return res

def pg_int(value):
    ''' Return PG date from datetime elements passed
    '''
    res = 'null'
    try:
        if value:
            return value
    except:
        pass
    return res

            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
