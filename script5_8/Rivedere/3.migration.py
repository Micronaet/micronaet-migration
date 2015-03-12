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
import sys, os

from openerp import migration
from openerp.utility import *
#from variables import table_migration
from variables_real import table_migration

# Tables v. 60:
openerp60 = migration.migration("Minerals60", "openerp", "30mcrt983")
# Tables v. 70:
openerp70 = migration.migration("Minerals70", "openerp", "30mcrt983")

# 3. valuto i campi diversi per modificare la select di partenza e quella di arrivo
# 4. valuto i campi relazione se va fatto un mapping al volo
# 5. leggo tutti gli id dei record presenti nella tabella di partenza

##################### METTERE IL CICLO #########################################
mapping_id = {} # dict that has all tables (name as key) mapped with record = {old_id: new_id}

tables = [
          #    'res_company', # NON FARE 1 record
          'res_users', # Mapping ID su login (primo effettuato)          
          #    'account_analytic_journal',  # Non viene eseguito (Mapping Manuale)
          'chemical_element',          # FATTO (RIATTIVARE)
          'chemical_product_category', # FATTO (RIATTIVARE)
          #'chemical_analysis',      # abbinati ai prodotti   >> dipende dai move_lines
          #'chemical_analysis_line', # abbinati alle analisi  >> dipende dai move_lines
          'product_product_analysis_model', # FATTO (RIATTIVARE)
          'product_product_analysis_line',  # FATTO (RIATTIVARE)
          'res_country', # Mapping di ID su code (sono già tutti presenti non è stata aggiornata la tabella solo tenuto il mapping di ID  (RIATTIVARE)
          'res_currency', # Mapping di ID su name  (RIATTIVARE)
          'res_country_state', # Mapping di ID su code  (RIATTIVARE)
          #'res_currency_rate', # NON FARE (ha solo da aggiornare il mapping che è corretto con l'import res_currency
          #'res_groups', # NON IMPORTATO (#TODO Se va importato occorre fare il mapping manuale per abbinare i gruppi vecchi ai nuovi!!!!!  << no key!
          #    'account_fiscal_position', # Non occorre hanno i record pari pari
          #    'res_partner_title', # Non occorre importare, tengo il mapping attuale anche se non è rispettatissimo
          'res_partner', # FATTO # 1 mapping di campo e delle proprietà ancora da importare
         ]

# Manual mapping_id: ***********************************************************
never_map_m2o_table = ['res_company',] # tabelle per i many2one che non richiedono il mapping (es. company è sempre 1)  >> aumenta con le tabelle che cancellano la destinazione
multi_loop_tables = ['res_partner',]
mapping_id['res_company'] = {1:1} # non cambio i campi: res_company (non dovrebbe più servire) 
mapping_id['account_analytic_journal'] = {1:1} # non cambio i campi: res_company (non dovrebbe più servire)
mapping_id['res_partner'] = {1:1}  # il primo partner è quello della company
# ******************************************************************************

total_loop = 1
for table in tables:
    if table in multi_loop_tables:
        total_loop = len(table_migration[table][2][0]) # multiloop tables have more than one sync key
        #import pdb; pdb.set_trace()
        
    for loop in range(0,total_loop): # fatto per le tabelle che richiedono N passate (vedi res partner per trovare l'id di sync)    
        # Read variabile setted up before:
        import_table = table_migration[table][0]
        delete_before = table_migration[table][1]
        if table_migration[table][2]:
            if type(table_migration[table][2]) in (type(()), type([])): # tuple:
                if type(table_migration[table][2][0]) in (type(()), type([])): # tuple (for res_partner)
                    key_field = table_migration[table][2][0][loop]  # take parameter depending on loop number
                else:
                    key_field = table_migration[table][2][0]   # if True need a sync, else only migration 
                key_field_force_update = table_migration[table][2][1]
            else:    
                key_field = table_migration[table][2]   # if True need a sync, else only migration 
                key_field_force_update = False
        else:
            key_field=False
            key_field_force_update = False
            
        many2one = openerp60.many2one(table.replace("_","."))
        many2one_fields = many2one[table].keys() if table in many2one else {}
        mapping_fields = table_migration[table][8]
        extra_field_defaults = table_migration[table][9] if len(table_migration[table])>=10 else {}
        select_list = table_migration[table][5]
        if mapping_fields: # add key to map (insetead of are not "selected" and there's no value
            select_list.extend(mapping_fields.keys())
        
        if delete_before: # Erase records (and save table for never_map_m2o_table (they are the same)
            never_map_m2o_table.append(table)
            openerp70.unlink(table)

        if import_table:    
            for item_id in openerp60.ids(table): # 6. leggo record per record l'id della lista:    # verifico i dati della select da utilizzare e l'ordine
                # ---------------------
                # leggo i dati dalla 6#
                # ---------------------
                record = openerp60.read(table, item_id, select_list)                
                record_dict = {} #TODO Valutare se si può già avere così (trasformato in dict)
                junk = map(lambda k, v: record_dict.update({k: v}), select_list, record)
                record_dict.update(extra_field_defaults) # if present add extra fields
                # -----------------------
                # Mapping di campo (key)#   << Eseguito prima per casi tipo country - country_id
                # -----------------------
                for key in mapping_fields.keys():
                    if key in record_dict:
                        record_dict[mapping_fields[key]] = record_dict[key] # update new key with old value
                        del record_dict[key]                               # remove field                
                    else:
                        print "#WARN Scritto male un mapping di field nel dict di importazione variabili: Tabella: %s Campo: %s:%s"%(table, key, mapping_field[key])
                        continue
                # -----------------------
                # Mapping di ID (value) #
                # -----------------------
                # mapping dei campi many2one (scambio ID se fa parte della mapping_id) # TODO << occorre verificare se è necessagio creare prima per dipendenza gli altri oggetti
                if table != "res_users":  # nel caso stia lavoranto con res_users salto il mappint (per l'id di creazione)
                    if many2one_fields: # if is present many2one record and not res_user # TODO ID!!
                        for m2o_field in many2one_fields:                                                
                        
                            if m2o_field[:9]=="property_":  # jump property for now! (m2o)
                                continue                    
                            elif m2o_field not in record_dict :
                                print "#WARN Mapping field not in record: Tabella: %s Campo m2o: %s"%(table, m2o_field) # può essere per le property
                                # non viene rimappato l'ip
                            else:
                                if record_dict[m2o_field]=='null': # TODO fare meglio!
                                    continue # non è presente l'ID
                                m2o_table = many2one[table][m2o_field].replace(".","_")
                                # field to mapping_id (or table with 0 records) # TODO il test è fatto sulla tables messa qui, sarebbe più corretto vedere se tabella con 0 record
                                if m2o_table not in never_map_m2o_table and m2o_table in tables: 
                                    if m2o_table in mapping_id: # test if is in the mapping list (remember for the one that there's   (TODO >>> uid <<<)                                    
                                        if record_dict[m2o_field] in mapping_id[m2o_table]:
                                            record_dict[m2o_field] = mapping_id[m2o_table][record_dict[m2o_field]]
                                        else:
                                            print "#ERR: ID non trovato tabella: %s campo: %d ID v.60: %s"%(table, m2o_field, record_dict[m2o_field])
                                    else:
                                        ####import pdb; pdb.set_trace()
                                        print "#WARN Mapping fallito: %s [%s >> %s] << vedere se è il caso di caricare prima la tabella del mapping e se cambia ID"%(table, m2o_field, m2o_table)
                    else: # mapping uid standard fileds created automatically from openerp,
                        for f in ['create_uid','write_uid']:
                            if f in record_dict and record_dict[f] in mapping_id['res_users']: # standard uid fileds (is present in 6.0 field list?)
                                # TODO attenzione se è null fallisce la precedente condizione quindi non viene aggiornato di fatto il campo
                                # Aggiorno l'utente da scrivere con il nuovo ID                            
                                record_dict[f] = mapping_id['res_users'][record_dict[f]] # vecchio ID utente diventa il nuovo
                updated = False
                # -----------------
                # Write or Create #
                # -----------------
                old_id = record_dict['id']            
                if key_field: # devo agganciare il record cercando se esiste già
                    if table not in mapping_id: 
                        mapping_id[table] = {} # add mapping ID element
                    #if record_dict[key_field]=="VEB": import pdb; pdb.set_trace()     <<< da tastase dopo un nuovo restore!
                    
                    if old_id in mapping_id[table]:        # caso particolare per res.partner ID 1    
                        to_update = True
                    else:    
                        to_update = openerp70.mapping_id(table, record_dict, key_field, mapping_id[table])
    
                    del record_dict['id'] # both create / update
                    if to_update: # else create after without ID
                        # Fare la procedura di aggiornamento solo per cambiare i campi many2one oppure per vedere variazioni in quelli già esistenti
                        if key_field_force_update:
                            openerp70.write(table, mapping_id[table][old_id], record_dict) 
                        updated = True
                    elif key_field_force_update: # solo per le tabelle a cui devo forzare la scrittura
                        if record_dict[key_field] == 'null':
                            updated = True # faccio finta che sia updated, dovrebbe aggiornarlo la prossima passata
                        else:    
                            # non dovrebbe passare qui!
                            print "#ERR non dovrebbe passare di qui!" #import pdb; pdb.set_trace()

                if not updated:
                    # verifico che non si debba fare un mapping di alcuni valori ID (campi many2one)
                    new_id = openerp70.create(table, record_dict)
                    if new_id and key_field:  # if record created and sync case:
                        mapping_id[table][old_id] = new_id  # save new ID (in dict of update + new)
                # scrivo nella nuova tabella i dati della select modificata in funzione delle colonne e dell'ordine e del mapping

            # After create all record update sequence:    
            set_next_id = openerp70.set_next_id(table)

            # salvo se occorre un record: oggetto, old, new (per eseguire futuri mapping)
print mapping_id            
del openerp70, openerp60
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
