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
import os
import sys
import psycopg2 #sudo apt-get install python-psycopg2
import xmlrpclib


# -----------------------------------------------------------------------------
#                                      CLASS
# -----------------------------------------------------------------------------

class server():
    ''' Class for manage OpenERP server (both: ORM, XMLRPC)
    '''
    
    # -------------------------------------------------------------------------
    #                               Private data
    # -------------------------------------------------------------------------
    
    # Common parameters:
    _dbname = False            # ORM and PG database name
    _host = False              # ORM and PG database host
    _verbose = False           # Verbose comunication

    # ORM parameters:
    _socket = False            # Socket for XML-RPC

    _orm_user = False          # XML-RPC user
    _orm_uid = False           # XML-RPC uid from socket authentication
    _orm_password = False      # XML-RPC password
    _orm_xmlrpc_port = False   # XML-RPC port
    
    # Postgres parameters
    _pg_connection = False     # Postgres object connection
    _pg_cursor = False         # Postgres cursor for query

    _pg_user = False           # Postgres user
    _pg_password = False       # Postgres password
    _pg_port = False           # Postgres port
    
    # -------------------------------------------------------------------------
    #                               Magic method
    # -------------------------------------------------------------------------
    def __init__(self, 
        dbname, host = "localhost", verbose = False, 
        orm_user = "admin", orm_password = "password", orm_port = 8070,
        pg_user = "openerp", pg_password = "password", pg_port = 5432, ):
        ''' Constructor for the class:        
        
            self: object reference
            dbname: database name
            host: host (both: pg - openerp)
            verbose: if operation on database generate log
            orm_user: XMLRPC user
            orm_password: XMLRPC password
            orm_port: XMLRPC 8070
            pg_user: Postgres user
            pg_password: Postgres password"
            pg_port: Postgres port
        '''
        
        # Initialize data elements for this class:
        self._dbname = dbname
        self._host = host
        self._verbose = verbose
        
        self._orm_user = orm_user
        self._orm_password = orm_password
        self._orm_port = orm_port
        
        self._pg_user = pg_user
        self._pg_password = pg_password
        self._pg_port = pg_port
        
        # ----------------------
        # Connection operations:
        # ----------------------

        # PG:        
        self._pg_connection = self._pg_connect() # TODO usare: psycopg2.connect(dsn, cursor_factory=DictCursor) 
        if self._pg_connection:
            self._pg_cursor = self._pg_connection.cursor()
        else:
            self._pg_cursor = False    

        # ORM:
        self._orm_connect()
        
     
    def __del__(self,):
        ''' Destroy the class:

            self: object reference
        ''' 
        try:
            # Close postgres object 
            if self._pg_cursor:              # close cursor
                self._pg_cursor.close()        
            if self._connection:             # close connection
                self._connection.close()        
            if self._socket:
                self._socket.close()         # Close XMLRPC connection

            # TODO to complete with XML-RPC
        except:
            pass   

    # -------------------------------------------------------------------------
    #                            Private method
    # -------------------------------------------------------------------------

    # ---------
    # Postgres:
    # ---------    
    def _pg_connect(self,):
        ''' Connect function to PG database:
        
            self: object reference
            @return connection for doing operations
        '''
        try:
            return psycopg2.connect(database = self._dbname,
                                    user = self._pg_user,
                                    password = self._pg_password,
                                    host = self._host,
                                    port = self._pg_port,)
        except:
            return False    

    # ----
    # ORM: 
    # ----
    def _get_uid(self, ):
        ''' Connect to XML-RPC server (login phase):

            self: object reference
        '''
        
        socket = xmlrpclib.ServerProxy(
            'http://%s:%s/xmlrpc/common' % (self._host, self._orm_port),
            allow_none = True)
        self._orm_uid = socket.login(
            self._dbname, self._orm_user, self._orm_password)
        if self._orm_uid:
            return True
        return False    
                                                        
    def _orm_connect(self, ):
        ''' Connect to XML-RPC server saving the socket in object private data:

            self: object reference
        '''
        if self._get_uid():
            self._socket = xmlrpclib.ServerProxy(
                'http://%s:%s/xmlrpc/object' % (self._host, self._orm_port),
                allow_none = True)
        else:
            self._socket = False

    # -------------------------------------------------------------------------
    #                           Public method
    # -------------------------------------------------------------------------
    
    # ---------
    # Postgres:
    # ---------    
    def pg_execute(self, query, need_commit = False, parameters = (), force_not_verbose = False): 
        ''' Execute the query using database connection / cursor:

            self: object reference
            query: query to execute
            need_commit: execute commit after query execution (for command q.)
            parameters: (not used for now) parameter for merge in the query
        '''
        
        if self._pg_cursor:
            self._pg_cursor.execute(query, parameters)
            if need_commit:
                self._pg_connection.commit()
            if self._verbose and not force_not_verbose:
                print query
        else:
            return False

    # ----
    # ORM:
    # ----
    def orm_execute(self, *parameters): 
        ''' Utility for not repear parameter for socket calls:

            self: object reference
            *parameters: list of extra parameters for the socket execute funct.
        '''
        
        return self._socket.execute(
            self._dbname, self._orm_uid, self._orm_password,
            *parameters) # enroll parameters list

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
