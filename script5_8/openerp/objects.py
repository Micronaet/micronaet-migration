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
from pg import * # utility for PG data conversion
from database.berkeley import berkeley


# -----------------------------------------------------------------------------
#                                      CLASS
# -----------------------------------------------------------------------------
class table():
    ''' Class for manage OpenERP table-object for migration 6-7
    '''

    # -------------------------------------------------------------------------
    #                               Private data
    # -------------------------------------------------------------------------
    # Common parameters:
    _name = False                  # Object name old (in o6 DB)
    _name_new = False              # Object name new (in o7 DB), usually = _name

    _table = False                 # Table name
    _table_new = False             # Table name new

    _key = False                   # Key field

    _o6 = False                    # OpenERP object V.6
    _o7 = False                    # OpenERP object V.7
    _field_mapping = False         # Dict with from (key) - to (value) mapping
    _mapping_databases = False     # Dict with berkeley mapping_tables

    # Features parameters:
    _static = False
    _manual_mapping = False        # Dict with key = old: value = new value (mapping during import)
    _command = []                  # Command to use (create, update, link)
    _remove_field = False          # List of fields to remove during importation
    _extra_migration = False       # Dict with passed list (extra migration loop)
    _extra_domain = False          # Extra domanin for search in 7 linked operation
    _source_domain = False         # Source (v.6) domain for search/read this record (case: recursione mrp.bom)
    #_source_order = None          # Force source order when read record in v.6
    
    # Calculated parameters:
    _6_field = False               # Dict of key=field value=type col in v.6
    _7_field = False               # Dict of key=field value=type col in v.7

    _6_and_7_field = False         # list of fields in 6 and 7 (to migrate)

    _m2m_list = False              # list of many2many fields
    _m2o_list = False              # list of many2one fields
    _o2m_list = False              # list of one2many fields (TODO check id mapping on that table)

    # -------------------------------------------------------------------------
    #                             Magic method
    # -------------------------------------------------------------------------
    def __init__(self, name, key, o6, o7, mapping_databases, name_new = False,
            field_mapping = None, static = None, command = None,
            remove_field = None, only_field = None,
            extra_migration = None, extra_domain = None, source_domain = None,
            #source_order = None,  
            manual_mapping = None):
        ''' Constructor for the class:

            self: Instance object
            name: name of the object (translated in table)
            key: key field for join with exist record
                 string > 'key' only one key
                 tuple, list > ['key1', 'key2']
            o6: openerp v.6 Object (for manage connection)
            o7: openerp v.7 Object (for manage connection)
            field_mapping: dict for mapping field / key name 6 > 7
            mapping_databases: dict with berkeley databases (tables) for map id
            static: dict if there's a static assignation (no migration)
            command: List of command used ['create', 'update', 'link']
                     'create' > only create record (automatic map link)
                     'update' > only update record (automatic map link)
                     'force_update_first' > in update operation if there's >1 record take first
                     'link'   > only map ID with existent record (raise error?)
                     'update_fixed_columns' > after import via XMLRPC write in PG 4 fixed columns
                     'reset_berkeley' > delete database file if present
                     >> use: ['create'], ['create', 'update'], ['update'], ['link']
            remove_field: List of fields to remove during record creation
            only_field: List of only field that need to migrate
            extra_migration: Dict with key = pass, value = field list << non credo si utilizzi per ora
            extra_domain: tuple for domain used in search 7 operation
            source_domain: used for filter read in old table (used for recursion like mrp.bom)
            # source_order: used for order record in read v.6 database << tolto per ora
            manual_mapping: dict if there's some particular case to map manually
        '''

        # Init fields:
        self._name = name
        self._name_new  = name_new if name_new else name

        self._table = self._name.replace(".", "_")
        self._table_new = self._name_new.replace(".", "_")

        # Mapping keys        
        self._key = key if type(key) in [list, tuple] else [key]
 
        self._o6 = o6
        self._o7 = o7

        # Set up objects not mandatory:
        self._field_mapping = {} if field_mapping is None else field_mapping
        self._manual_mapping = {} if manual_mapping is None else manual_mapping
        self._static = {} if static is None else static
        self._command = [] if command is None else command
        self._remove_field = [] if remove_field is None else remove_field
        self._only_field = [] if only_field is None else only_field
        self._extra_migration = {} if extra_migration is None else extra_migration
        self._extra_domain = () if extra_domain is None else extra_domain
        self._source_domain = () if source_domain is None else source_domain
        #self._source_order = source_order

        # Add this object as a berkeley DB:
        self._mapping_databases = mapping_databases
        if self._name not in self._mapping_databases: # not yet created / linked
            self._mapping_databases[self._name] = berkeley(self._o6._dbname, self._name, force_reset = 'reset_berkeley' in self._command)

        # Calculated fields:
        self._6_field = self._get_column_dict(self._o6)
        self._7_field = self._get_column_dict(self._o7)
        self._6_and_7_field = self._get_6_and_7()

        self._m2o_list = self._get_column_type(self._6_field, 'many2one')
        self._m2m_list = self._get_column_type(self._6_field, 'many2many')
        self._o2m_list = self._get_column_type(self._6_field, 'one2many')

    # -------------------------------------------------------------------------
    #                             Private method
    # -------------------------------------------------------------------------

    # -----------------------------------
    # List of fields in v.6 or / and v.7:
    # -----------------------------------
    def _get_column_dict(self, openerp):
        ''' Get column dict (column: type) >> search in ir_model_fields table
            >> ttype = (reference, serialized, datetime, many2many, text,
                       selection, float, one2many, binary, char, many2one,
                       html, date, boolean, integer, )

            self: object reference
            openerp: openerp object (for connection with database)
            @return: dict with key = column name, value = (type of field, [object], )
        '''
        res = {}
        field_ids = openerp._socket.execute(
            openerp._dbname, openerp._orm_uid, openerp._orm_password,
            'ir.model.fields', 'search', [('model', '=', self._name)], )

        for field in openerp._socket.execute(
            openerp._dbname, openerp._orm_uid, openerp._orm_password, 'ir.model.fields',
            'read', field_ids, ):
            if field['ttype'] in ('many2one', 'many2many', 'one2many', ):
                res[field['name']] = (field['ttype'], field['relation'])
            else: # normal field:
                res[field['name']] = (field['ttype'], )
        return res

    def _get_6_and_7(self, ):
        ''' Column in 6 and 7:

            self: object reference
        '''

        return [key for key in self._6_field if key in self._7_field]

    # ------------------------------------
    # list of particular columns / fields:
    # ------------------------------------
    def _get_column_type(self, field_list, field_type):
        ''' Search only in v.6 openerp database:

            self: object reference
            field_list: dict with {col name: field type}
            field_type: field type searched in the field_list
            @return: list of field found
        '''

        return [key for key in field_list if field_list[key][0] == field_type]

    # -------------------
    # information method:
    # -------------------
    def _total_record(self, openerp):
        ''' Search v.6 openerp table:

            self: object reference
            openerp: openerp object
            @return: total record found
        '''
        try:
            openerp.pg_execute("SELECT count(*) FROM %s;" % (self._table, ), force_not_verbose = True)
            record = openerp._pg_cursor.fetchone()
            return record[0]
        except:
            return "#ERR"

    # ------------------------
    # update records function:
    # ------------------------
    def _update_fixed_field(self, ):
        ''' Read in v.6, update in v.7
            create_uid, create_date, write_uid, write_date:

            self: object reference

        '''
        if not self._o6._pg_cursor:
            return False

        query = "SELECT id, create_uid, write_uid, create_date, write_date FROM %s;" % (self._table_new, )
        self._o6.pg_execute(query, force_not_verbose = True)

        for record in self._o6._pg_cursor.fetchall():
            query = "UPDATE %s SET create_uid = %s, write_uid = %s, create_date = %s, write_date = %s WHERE id = %s;" % (
                self._table_new,
                pg_int(self._mapping_databases["res.users"].read(record[1])),
                pg_int(self._mapping_databases["res.users"].read(record[2])),
                pg_datetime(record[3]),
                pg_datetime(record[4]),
                self._mapping_databases[self._name].read(record[0]),
            )
            self._o7.pg_execute(query, need_commit = True, force_not_verbose = True)
        return True

    # --------
    # Utility:
    # --------
    def _remapping_object_id(self, table, old_id):
        ''' Utility for read in Berkeley mapping DB the old record in table
            selected

            self: object reference
            table: table name (database name)
            old_id: old ID value
            @return: new ID (if present else 0) # TODO check if mandatory!
        '''

        if table in self._mapping_databases: # Berkeley present
            new_id = self._mapping_databases[table].read(old_id)
            if new_id:
                return new_id
            else:
                print "# ERROR: Table %s in relation with %s has no ID old: %s new: %s" % (
                    self._name, table, old_id, new_id)
        else:
            print "# ERROR: Table %s in relation with %s create before the object" % (
            self._name, relation_object)
        return 0  # TODO eventualmente se è se obbligatorio (0 da errore in scrittura)

    # -------------------------------------------------------------------------
    #                           Public method
    # -------------------------------------------------------------------------
    def migrate_many2many(self, field_name):
        ''' Migrate many2many values
        
            self: object reference
        '''
        if self._o6._verbose:
            print "Start migration many2many fields: %s > %s" % (self._name, field_name)
        
        # ----------------------------------
        # Open source records with m2m field
        # ----------------------------------        
        record_ids = self._o6.orm_execute(self._name, 'search', [])
        for record in self._o6.orm_execute(self._name, 'read', record_ids, ('id', field_name,)):
            old_id = record['id']
            new_id = self._mapping_databases[self._name].read(old_id)
            
            if not record[field_name]: 
                continue # with next
                
            # Create new record for update m2m fields with current mapping ID:
            destination_table = self._6_field[field_name][1]
            if destination_table not in self._mapping_databases:
                print "Berkeley database not found for: %s" % (destination_table)
            record_m2m = [self._mapping_databases[destination_table].read(item_id) for item_id in record[field_name]]
            
            # Write existent destination:
            if new_id: # new record not present
                self._o7.orm_execute(self._name_new, 'write', new_id, {field_name: [(6, 0, record_m2m)] })
            else:
                print "many2many field new ID not found: %s table: %s" % (new_id, self._name_new)     
        return
        
    def migrate(self, migration_pass = False):
        ''' Migration of the table from o6 to o7:

            self: object reference
            migration_pass: for more pass of migration (usually 0), see self._extra_migration
        '''
        error = "starting migration..."
        if self._o6._verbose:
            print "Start migration: %s" % (self._name)

        # ---------------------
        # Test if no migration:
        # ---------------------
        error = "test if there's a n step migration loop..."
        if migration_pass:
            if migration_pass not in self._extra_migration:
                print "Error, migration pass not present"
            else:
                migration_pass_list = self._extra_migration[migration_pass]
        # TODO: manage migration_pass_list

        error = "test if there' manual / static migration..."
        if self._static:
            # ------------------------------------------------------------------
            # Manual migration (only mapping ID)
            # ------------------------------------------------------------------
            for key in self._static:
                self._mapping_databases[self._name].write(key, self._static[key])
        else:
            # ------------------------------------------------------------------
            # Automatic Migration (1x1) 6 & 7 + mapping list:
            # ------------------------------------------------------------------
            error = "automatic migration started (only some field test)..."
                        
            if self._only_field: # List of the only field to keep
                # ------------------------
                # Keep only field columns:
                # ------------------------
                cols = self._only_field[:]                                     # copy list

            else: # calculate list (6 AND 7 + mapping fields):
                # ------------------------
                # Keep only 6 AND 7 fields + mapping fields:
                # ------------------------
                cols = self._6_and_7_field[:]  # copy list

            error = "add extra key in column list..."
            cols.extend([k for k in self._key if k not in cols])           # add key field
            cols.extend([k for k in self._field_mapping if k not in cols]) # add mapping field

            if 'id' not in cols: # Always present!
                cols.append('id')

            # ----------------------------
            # Remove calculated data cols:
            # ----------------------------
            error = "start removing columns manually passed..."
            
            remove_cols = []
            if self._remove_field: # Add forced remove cols
                remove_cols.extend(self._remove_field)

            error = "start remove relation fields..."
            for remove_field in (
                    'function', 'relation', 'one2many', 'many2many',
                    'reference', 'serialized', ): # TODO per le property? 'related',  << sembra che non ci siano i campi property, function e relation
                remove_cols.extend(self._get_column_type(self._6_field, remove_field))

            error = "remove phisically the columns from list..."
            # Remove fisically col in cols list:
            for col in remove_cols:
                if col in cols:
                    cols.remove(col)

            # ----------------------------------
            # Loop on every record for creation:
            # ----------------------------------
            error = "start migration loop (append extra domain)..."
            source_domain = []
            
            if self._source_domain:
                source_domain.append(self._source_domain)
            #if self._source_order:
            #    import pdb; pdb.set_trace()    
            #    record_ids = self._o6.orm_execute(self._name, 'search', source_domain, 0, 0, self._source_order)
            #else:
            error = "start searching..."
            record_ids = self._o6.orm_execute(self._name, 'search', source_domain)
            # Problema: il read non legge i record nell'ordine del search
            #if self._source_order:
            # Always sort per ID:
            
            error = "start reading..."
            record_unsorted = self._o6.orm_execute(self._name, 'read', record_ids, cols)
            #if 'source_order_as_is' in self._command:
            #    records = record_unsorted
            #else:    
            #    error = "start sorting..."
            records = sorted(record_unsorted, key = lambda k: k['id'])     
                
            error = "loop for creations..."
            for record in records:
                old_id = record['id']
                #record_old = record[:]

                # -----------------------------------------
                # Convert many2one field (also mapping ID):
                # -----------------------------------------
                error = "convert m2o with mapped ID in new version..."
                # TODO test for property many2one (and other type)
                for m2o_col in self._m2o_list:
                    if m2o_col in record and record[m2o_col] and type(record[m2o_col]) in (list, tuple) and len(record[m2o_col]) == 2: # there's a value
                        #m2o_name = self._field_mapping.get(m2o_col, m2o_col)
                        record[m2o_col] = self._remapping_object_id(
                            self._6_field[m2o_col][1], record[m2o_col][0])
                        #   self._7_field[m2o_col][1], record[m2o_col][0])
                        # TODO testare bene, è stato messo 7 al posto di 7 in consequenza a res.partner.address

                # -------------------------------
                # Remove unused fields (like ID):
                # -------------------------------
                del(record['id']) # NOTE: before remapping columns!

                # ----------------------------
                # Mapping column if present:
                # ----------------------------
                error = "mapping column name if passed..."
                for old_field in self._field_mapping: # key and field re-mapping
                    record[self._field_mapping[old_field]] = record[old_field]
                    del record[old_field]

                # ---------------------------------------------
                # Add extra v.7 field (if defaults is present): TODO
                # ---------------------------------------------

                # --------------------------
                # Search record in Berkeley:
                # --------------------------
                error = "search new record in Berkeley..."
                if self._name_new == self._name:
                    new_id = self._mapping_databases[self._name].read(old_id)
                else:
                    new_id = False # always try to update (es. res.partner.address)

                # test if is present id
                error = "if not present start compose domain for search..."
                if not new_id:
                    domain = []
                    if self._extra_domain:
                        domain.append(self._extra_domain)
                    if old_id in self._manual_mapping:   # composed with key passed (or manual map)
                        domain.append(('id', '=', self._manual_mapping[old_id]))
                    else:                                # calculated with key (test if remapped key)
                        for k in self._key:
                            key_name = self._field_mapping.get(k, k) # else take k
                            domain.append((key_name, '=', record[key_name]))

                    error = "search in new database..."
                    new_ids = self._o7.orm_execute(self._name_new, 'search', domain)
                    if len(new_ids) == 1:   # OK
                        new_id = new_ids[0]
                    elif len(new_ids) > 1:  # KO
                        error = "test if there's a ID force update befor link to new..."
                        if 'force_update_first' in self._command:
                            new_id = new_ids[0] # take first
                        else:
                            print "# Object: %s > %s >> Error more than one record, no key value: %s (jumped)" % (self._name, self._name_new, new_ids)
                            continue
                    # else test next bloc

                # -----------------------
                # create / update record:
                # -----------------------
                error = "create / update record..."
                try:
                    # Particular cases:
                    # Case: yet deleted but, if remapping key field, will return
                    error = "re-remove extra fields..."
                    if 'id' in record:
                        del(record['id']) 
                    # Case: 3 inherit (es. product_templ_id, is reloaded in read method)    
                    for remove in self._remove_field:
                        if remove in record:
                            del(record[remove])

                    error = "test if create or update..."
                    if new_id: # new record not present
                        if 'update' in self._command:
                            error = "updating record..."
                            self._o7.orm_execute(self._name_new, 'write', new_id, record)

                    else:          # new record present
                        if 'create' in self._command: # no new ID and command create
                            error = "creating record..."
                            new_id = self._o7.orm_execute(self._name_new, 'create', record)

                    # Write mapping in Berkeley DB:
                    error = "writing in Berkeley DB..."
                    if new_id: # create / update / link:
                        self._mapping_databases[self._name].write(old_id, new_id)
                    else:
                        print "Berkeley new ID not present, Table:", self._name, "obj", self._name_new, "ID", old_id # %s > %s >> ID % (v.6) not found!" % (self._name, self._name_new, old_id)
                    #print "%s\nold:\t%s [%s]\nnew: %s [%s]" % (self._name, old_id, record_old, new_id, record)

                except: # Error no record is created!! # TODO Manage error
                    print "#ERR [%s] Object: %s > %s >> Generic error during importation: %s" % (error, self._name, self._name, sys.exc_info(), )
                    #import pdb; pdb.set_trace()
                    continue

        # ----------------------------------
        # Adjust creation standard 4 fields:
        # ----------------------------------
        if 'update_fixed_columns' in self._command:
            self._update_fixed_field()

        # ----------------------
        # Sync database to disk:
        # ----------------------
        self._mapping_databases[self._name]._db.sync()

        # ----------------
        # Verbose comment:
        # ----------------
        if self._o6._verbose:
            self.info(importation = True)
        return

    def info(self, importation = False):
        ''' Function for print information about private parameter of the obj

            self: object reference
        '''
        if importation:
            print """
===============================================================================
| - Object: %s - %s >> Table: O: %s-N: %s [Key: %s]
|
| - Mapping field: %s
| - Manually ID: %s
|
| - Commands: [%s]
|
| - Field dict 6: %s
| - Field dict 7: %s
|
| - Field 6: %s
| - Field 7: %s
| - Field 6 and 7: %s
|
| - M2O field: %s
| - M2M field: %s
| - O2M field: %s
|
| - Total [v.6: %s] [v.7: %s]
===============================================================================
""" % (
            self._name,
            self._name_new,
            self._table,
            self._table_new,
            self._key,
            self._field_mapping,
            self._static,
            self._command,
            self._6_field,
            self._7_field,
            self._6_field.keys(),
            self._7_field.keys(),
            self._6_and_7_field,
            [(k, v[1]) for (k, v) in self._6_field.iteritems() if k in self._m2o_list],
            [(k, v[1]) for (k, v) in self._6_field.iteritems() if k in self._m2m_list],
            [(k, v[1]) for (k, v) in self._6_field.iteritems() if k in self._o2m_list],
            self._total_record(self._o6),
            self._total_record(self._o7),
            )
        else:
            print """
===============================================================================
| - Object: %s - %s >> Table: O: %s-N: %s [Key: %s]
|
| - o6: %s - o7: %s
|
| - Mapping field: %s
| - Berkeley: %s
|
| - Manually id: %s
|
| - Command: [%s]
|
| - Field dict 6: %s
| - Field dict 7: %s
| - Field 6: %s
|
| - Field 7: %s
| - Field 6 and 7: %s
|
| - M2O field: %s
| - M2M field: %s
| - O2M field: %s
|
| - Total [v.6: %s] [v.7: %s]
===============================================================================
""" % (
            self._name,
            self._name_new,
            self._table,
            self._table_new,
            self._key,
            self._o6,
            self._o7,
            self._field_mapping,
            self._mapping_databases,
            self._static,
            self._command,
            self._6_field,
            self._7_field,
            self._6_field.keys(),
            self._7_field.keys(),
            self._6_and_7_field,
            [(k, v[1]) for (k, v) in self._6_field.iteritems() if k in self._m2o_list],
            [(k, v[1]) for (k, v) in self._6_field.iteritems() if k in self._m2m_list],
            [(k, v[1]) for (k, v) in self._6_field.iteritems() if k in self._o2m_list],
            self._total_record(self._o6),
            self._total_record(self._o7),
            )
        return

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
