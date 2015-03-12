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
import psycopg2 #sudo apt-get install python-psycopg2
import sys, os

# ---------------
# Class:
# ---------------

class migration():
    ''' Class for manage migration operation like:
        connect to a database
        launch select query
        launch command query
    '''
    import psycopg2
    
    # ------------------
    # Magic functions: -
    # ------------------    
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        ''' Init script of the class
        '''
        # Initialize data elements for this class:
        self._dbname = dbname
        self._user = user
        self._password = password
        self._host = host
        self._port = port
        self._verbose = True # set to false if don't want
        
        self._connection = self.connect(dbname, user, password, host, port)
        # TODO usare: psycopg2.connect(dsn, cursor_factory=DictCursor) 
        if self._connection:
            self._cursor = self._connection.cursor()
        else:
            self._cursor = False    
     
    def __del__(self,):
        ''' Destroy the class
        ''' 
        try:
            if self._cursor:              # close cursor
                self._cursor.close()        
            if self._connection:          # close connection
                self._connection.close()        
        except:
            pass   
                            
    # ------------------
    # Hide functions:  -
    # ------------------    
    def _value_list2string(self, values):
        ''' Convert a list of values in string list for create method
        '''
        return ("%s"%(values,))[1:-1].replace("'null'","null") # turn list in string text

    def _field_list2string(self, fields):
        ''' Convert a list of values in string list for create method
        '''
        return ("%s"%(fields,))[1:-1].replace("'","").replace("\"","") # turn list in string text
                            
    def connect(self, dbname, user, password, host="localhost", port=5432):
        ''' Connect function to 
            dbname: database name
            user: user name
            host: hostname (default localhost)
            port: port (default 5432)
            @return connection for doing operations
        '''
        try:
            return psycopg2.connect(database=dbname,
                                    user = user,
                                    password = password,
                                    host = host,
                                    port = port,
                                    )            
        except:
            return False    

    def execute(self, query, parameters = ()): 
        ''' Execute the query using database create at star
        '''
        if self._cursor:
            return self._cursor.execute(query, parameters)
        else:
            return False    

    def many2one(self, table=""):
        ''' Read ir.model.fields and get all the list of many2one fiels
            return a dict with key all table or table passed, value=
            field_name: relation_object
        '''
        res = {}
        if self._cursor:        
            where = "where %s ttype='many2one'"%("model = '%s' and"%(table,) if table else "")
            #                              0      1      2
            self._cursor.execute("select model, name, relation from ir_model_fields %s;"%(where,))
            for field in self._cursor.fetchall():
                model = field[0].replace(".","_")
                if model not in res:
                    res[model]={}
                res[model][field[1]]=field[2]
        
        return res
        
    def table_2_file(self, table, file_name): 
        ''' Copy all table data to file
        '''
        if self._cursor:
            return self._cursor.execute("COPY %s TO '%s'"%(table, file_name))
        else:
            return False    

    def ids(self,table, ):
        ''' Read the table and return the ids list
        '''
        res = []           
        if not self._cursor:
            return res

        query = "SELECT id FROM %s;"%(table,)
        self._cursor.execute(query) 
        if self._verbose:
            print query
            
        for record in self._cursor.fetchall():
            res.append(record[0])
        return res    

    def set_next_id(self, table):
        ''' read max id of record 
            update "*_id_seq" sequence with the next value
        '''
        if not self._cursor: return False # Error 

        query = "SELECT max(id) as max FROM %s;"%(table,)
        self._cursor.execute(query) 
        if self._verbose:
            print query

        try: # update sequence to next id
            record = self._cursor.fetchone()
            next = (record[0] or 0) + 1
            self._cursor.execute("ALTER SEQUENCE %s_id_seq RESTART WITH %s;"%(table, next))  # no comit operations!
            return True
        except:
            print "Error updating: %s > %s_id_seq"%(table, table)
            return False    
            
    # --------------------------
    #        ORM Method        -
    # --------------------------
    
    def read(self, table, item_id, fields = []):     
        ''' return the record id request, for the table, with select parameters list
        '''
        import datetime
        import decimal
        res = []
        
        if fields:
            fields = ("%s"%(fields,))[1:-1].replace("'","").replace("\"","") # turn list in string text
        else:
            fields = "*"
            
        if not self._cursor: return res

        query = "SELECT %s FROM %s WHERE id = %s;"%(fields, table, item_id)
        self._cursor.execute(query) 
        if self._verbose:
            print query

        record = self._cursor.fetchone()
        type_datetime = type(datetime.datetime.now())
        type_date = type(datetime.date(2012,12,23))
        type_decimal = type(decimal.Decimal(0.0))

        for item in record:
            # Solve (badly) cast problem with object readed:
            if type(item) in (type_datetime, type_date):                     # date and datetime value
                res.append(str(item))
                
            elif item is None:                                               # Null/None value 
                res.append("null")
                
            elif type(item) == type_decimal:                                 # Decimal
                res.append(float(item))                    
                
            else:                                                            # Normal append
                res.append(item)                
        return res

    def create(self, table, record_dict):
        ''' Create method: record list of values in the table password with the fields 
            order
        '''
        import sys
        
        if not record_dict:
            return False
            
        # TODO optimize:
        values = self._value_list2string(record_dict.values())      
        fields = self._field_list2string(record_dict.keys())     
            
        if not self._cursor: return False

        try:
            query = "INSERT INTO %s (%s) VALUES (%s) RETURNING id;"%(table, fields, values)
            self._cursor.execute(query) 
            if self._verbose:
                print query            
            self._connection.commit()  
            if 'id' in record_dict:
                new_id = record_dict['id']
            else:
                new_id = self._cursor.fetchone()[0] # save ID # TODO non funziona il fetchone alla fine!!!   <<<< funziona con returning id
                if not new_id: print "#ERR non viene letto l'id del record creato senza passare id"
                
            return new_id
        except:
            self._connection.rollback()
            print "#ERR: ", query, sys.exc_info()
            return False

    def write(self, table, item_id, record_dict):
        ''' Write record list of values in the table password with the fields 
            order
        '''
        import sys        
        if not record_dict or not item_id:
            return False # error
            
        # TODO optimize:
        #values = self._value_list2string(record_dict.values())      
        #fields = self._field_list2string(remapping_id(cord_dict.keys()))
        if not self._cursor: return False

        try:
            query = "UPDATE %s SET %s WHERE id=%s;"%(table, 
                                                     ", ".join(["%s='%s'"%(k,v) for k,v in record_dict.iteritems() if v!='null']),
                                                     item_id,
                                                     ) 
            #import pdb; pdb.set_trace()                                         
            self._cursor.execute(query)
            if self._verbose:
                print query
            
            self._connection.commit()
            return True
        except:
            self._connection.rollback()
            print "#ERR: ", query, sys.exc_info()
            return False
                
    def unlink(self, table):    
        ''' Delete all record in the table
        '''
        if not self._cursor:
            return False
        try:    
            query = "DELETE FROM %s;"%(table,)
            self._cursor.execute(query) 
            if self._verbose:
                print query

            self._connection.commit()
            return True
        except:
            print "#ERR", query
            return False

    # --------------------------
    #      end ORM Method      -
    # --------------------------

    def tables(self,):
        ''' Read table list and return the list of tables
        '''
        res = []
        if not self._cursor:
            return res
            
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        self._cursor.execute(query) 
        if self._verbose:
            print query

        for table in self._cursor.fetchall():
            #cursor.execute("SELECT count(*) FROM %s;"%(line))
            res.append(table[0])
        return res    
        
    def tables_count(self, ):
        ''' Read all tables of the DB and return a dict of tables with number
        '''
        res = {}
        if not self._cursor:
            return res
            
        for table in self.tables():
            self._cursor.execute("SELECT count(*) FROM %s;"%(table))        
            res[table]= self._cursor.fetchone()[0]
        return res    
    
    def get_column_list(self, table):    
        ''' Get list of colum for passed table
        '''
        res = []
        if not self._cursor:
            return res
            
        query = "SELECT column_name FROM information_schema.columns WHERE table_name = '%s';"%(table,)
        self._cursor.execute(query) 
        if self._verbose:
            print query

        for table in self._cursor.fetchall():
            res.append(table[0])
        return res    

    def mapping_id(self, table, record_dict, key_field, mapping_id):
        ''' Create a dict for mapping record baset on key field passed, if not
            present the ID is not created
        '''
        if record_dict[key_field]:
            self._cursor.execute("SELECT id FROM %s WHERE %s='%s';"%(table, key_field, record_dict[key_field]))
            new_id =  self._cursor.fetchone()
            if not new_id:
                # Non trovata corrispondenza, record da create
                print "#WARN Non trovata corrispondenza, record da creare"
                return False                
            elif len(new_id) == 1: # if is a key so theres' only one
                mapping_id[record_dict['id']] = new_id[0]
                return True
            elif len(new_id) > 1:
                print "#ERR Il campo chiave sembra avere più ricorrenze! Cosa fare?"
                ####import pdb; pdb.set_trace()
                # torno il primo??
                mapping_id[record_dict['id']] = new_id[0]
                return True
                # cosa fare??
                
        return False # record da creare         
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
