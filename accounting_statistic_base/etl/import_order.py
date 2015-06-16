#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ETL. import csv file with preformatted data comes from Mexal orders
# use: import.csv mexal_file_csv.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser
from posta import *
import sys, time, os # for get date of file

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import.py ocdetoerp.FIA
         *********************
         """ 
   sys.exit()

# Funzioni:
def prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def prepare_date(valore):
    valore=valore.strip()
    if len(valore)==8:
       if valore: # TODO test correct date format
          return valore[:4] + "/" + valore[4:6] + "/" + valore[6:8]
    return '' #time.strftime("%d/%m/%Y") (per gli altri casi)

def prepare_float(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values
       
def get_partner_id(sock, uid, pwd, mexal_id):
    ''' Ricavo l'ID del partner dall'id di mexal
    '''
    item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', mexal_id)])
    if item_id:
       return item_id[0]
    return 0   

FileInput=sys.argv[1]
if FileInput:
   sigla_azienda=FileInput[-3:].lower()
else:
   print "[ERR] File input non presente!"
   sys.exit()   
if sigla_azienda in ('gpb','fia'):
   cfg_file=sigla_azienda + ".openerp.cfg"
else:
   print "[ERR] Sigla azienda non trovata!"
   sys.exit()        
    
# Ricavo la data del file per comunicarla
create_date=time.ctime(os.path.getctime(FileInput))    

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname = config.get('dbaccess','dbname')
user = config.get('dbaccess','user')
pwd = config.get('dbaccess','pwd')
server = config.get('dbaccess','server')
port = config.get('dbaccess','port')   # verify if it's necessary: getint
separator = config.get('dbaccess','separator') # test
verbose = eval(config.get('import_mode','verbose')) #;verbose=True

verbose= False # TODO togliere

smtp_sender = config.get('smtp', 'sender')
smtp_receiver = config.get('smtp', 'receiver')
smtp_subject = config.get('smtp', 'subject') + " (Importazione Ordini e verifica date files)"
smtp_text = config.get('smtp', 'text')
smtp_log = config.get('smtp', 'log_file') + ".ordini.csv"
smtp_server = config.get('smtp', 'server')
#verbose_mail: True

debug_mode=True # TODO reset false when OK

# Open file log error (if verbose mail the file are sent to admin email)
try: 
   out_file = open(smtp_log,"w")
except:
   print "[WARNING]","Error creating log files:", smtp_log
   # No raise as it'a a warning

header_lines = 0 # mai da mexal
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
lines = csv.reader(open(FileInput,'rU'),delimiter=separator)   # prima era: rb
counter={'tot':-header_lines,'new':0,'upd':0,'order':0} # tot negative (jump N lines)

# Elimino tutti gli elementi della tabella prima di procedere all'importazione:
header_ids = sock.execute(dbname, uid, pwd, 'statistic.header', 'search', []) 
response =  sock.execute(dbname, uid, pwd, 'statistic.header', 'unlink', header_ids) 

order_ids = sock.execute(dbname, uid, pwd, 'statistic.order', 'search', []) 
response =  sock.execute(dbname, uid, pwd, 'statistic.order', 'unlink', order_ids) 

# Carico gli elementi da file CSV:
tot_col = 0
header_id = 0
old_order_number = ''
sequence = 0
try:
    for line in lines:
        if tot_col==0: # memorizzo il numero colonne la prima volta
           tot_col=len(line)
           print "[INFO] Colonne rilevate", tot_col
           raise_error("[INFO] Procedura: %s \n\tFile importato: %s [creazione: %s]"%(sys.argv, FileInput, create_date), out_file)
        if counter['tot']<0:  # salto le N righe di intestazione
           counter['tot']+=1
        else:   
           if len(line) and (tot_col==len(line)): # salto le righe vuote e le righe con colonne diverse
               counter['tot']+=1 
               try:
                   csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                   mexal_id = prepare(line[csv_id])
                   csv_id+=1      # Cliente descrizione
                   cliente = prepare(line[csv_id]) 
                   csv_id+=1      # Order number
                   number = prepare(line[csv_id])
                   csv_id+=1      # Data OC formato: YYYYMMDD
                   order_date = prepare_date(line[csv_id]) or False
                   csv_id+=1      # Scadenza OC formato: YYYYMMDD
                   order_deadline = prepare_date(line[csv_id]) or False
                   csv_id+=1      # Articolo
                   articolo_id = prepare(line[csv_id]) 
                   csv_id+=1      # Articolo descrizione   (oppure campo campo note nelle righe (D)escrittive )
                   articolo = prepare(line[csv_id]) 
                   csv_id+=1      # Quantity
                   quantity = prepare_float(line[csv_id]) or 0.0
                   csv_id+=1      # Tipo di riga (b si intende prodotto)
                   type_of_line = prepare(line[csv_id]) 
                   csv_id+=1      # Note
                   note = prepare(line[csv_id]) 

                   csv_id+=1      # Descrizione italiano
                   product_description = prepare(line[csv_id]) 
                   csv_id+=1      # Descrizione inglese
                   product_description_eng = prepare(line[csv_id]) 
                   csv_id+=1      # Numero colli
                   colli = prepare(line[csv_id]) 
                   csv_id+=1      # Tipo di riga (A o D)
                   line_type = prepare(line[csv_id]).lower() # a=articolo, d=descrizione

                   csv_id+=1      # Codice porto
                   port_code = prepare(line[csv_id]).lower()
                   csv_id+=1      # Descrizione italiano
                   port_description = prepare(line[csv_id]) 
                   csv_id+=1      # Destinazione descrizione
                   destination_description = prepare(line[csv_id]) 
                   csv_id+=1      # Destinazione indirizzo
                   destination_address = prepare(line[csv_id]) 
                   csv_id+=1      # Destinazione CAP
                   destination_cap = prepare(line[csv_id]) 
                   csv_id+=1      # Destinazione localita'
                   destination_loc = prepare(line[csv_id]) 
                   csv_id+=1      # Destinazione provincia
                   destination_prov = prepare(line[csv_id]) 

                   # Videata extra:
                   csv_id+=1      # Data di registrazione
                   registration_date = prepare_date(line[csv_id]) or False
                   csv_id+=1      # Note aggiuntive (nella stampa)
                   extra_note = prepare(line[csv_id]) 
                   csv_id+=1      # Note aggiuntive (nella stampa)
                   agent_description = prepare(line[csv_id]) 

                   # Calculated field:
                   # Dati dimensionali letti dal prodotto:
                   product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id','=', articolo_id )])  

                   if product_ids and line_type == 'a':
                       product_item = sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids)[0]
                       total_linear_meter = (quantity or 0.0) * product_item['linear_length']
                       total_volume = (quantity or 0.0) * (product_item['volume'] or 0.0)
                       total_weight = (quantity or 0.0) * (product_item['weight'] or 0.0)
                   else: # description line
                       total_linear_meter = False 
                       total_volume = False 
                       total_weight = False 

                       if line_type == "a": 
                          raise_error("[ERR] Riga:%s - Prodotto non trovato: %s"%(counter['tot'], articolo_id), out_file)
                   
                   total=0 #TODO
                   partner_id = get_partner_id(sock, uid, pwd, mexal_id)

                   if line_type=="a":
                      if not colli:
                         colli = quantity # se non ci sono i colli metto uguale a quantity (per avere il 20 x 1)
                   if port_code not in ('', 'f', 'a', 'd'):
                      raise_error("[ERR] Riga:%s - Codice Porto non trovato: %s"%(counter['tot'], port_code), out_file)

                   if line_type not in ('a', 'd'):
                      raise_error("[ERR] Riga:%s - Tipo di linea non trovato: %s"%(counter['tot'], line_type), out_file)
                      
                   if not partner_id:
                      raise_error("[ERR] Riga:%s - Partner non trovato: %s"%(counter['tot'], mexal_id), out_file)

                   if type_of_line.lower() == 'b':
                      quantity_ok = quantity or 0.0
                   else:
                      quantity_ok = 0.0
                       
                   if not number:   
                      raise_error("[ERR] Riga:%s - Numero d'ordine non trovato: %s"%(counter['tot'], number), out_file)
                      
                   # Inserimento ordine testata statistic.header
                   if old_order_number != number: # se cambia faccio le verifiche o lo creo altrimenti rimane l'ID prec.
                       old_order_number = number # memorizzo il vecchio numero
                       counter['order']+=1
                       sequence = 1
                       header = {'name': number, #"Ordine n.:%s"%(number,),
                                 'partner_id': partner_id,
                                 'date': order_date,
                                 'deadline': order_deadline,
                                 #'total': fields.float('Total', digits=(16, 2)),
                                 'note': note,
                                 'port_code': port_code,
                                 'port_description':port_description,
                                 'destination':destination_description,
                                 'destination_address': destination_address,
                                 'destination_cap': destination_cap,
                                 'destination_country': destination_loc,
                                 'destination_prov': destination_prov,
                                 'agent_description': agent_description,
                                 # extra window:
                                 
                                 'registration_date': registration_date,
                                 'extra_note': extra_note,                                 
                                }
                       # TODO ottimizzabile cercando la rottura di codice:       
                       search_header_id = sock.execute(dbname, uid, pwd, 'statistic.header', 'search', [('name','=',number)])
                       if search_header_id:
                          header_id=search_header_id[0] # Memorizzo per associarlo poi all'ordine
                       else: # Creo:
                           try:
                              header_id = sock.execute(dbname, uid, pwd, 'statistic.header', 'create', header)
                           except:
                              raise_error("[ERR] Riga:%s - Errore creando header: %s"%(counter['tot'], number), out_file)
                           if verbose: 
                              raise_error("[INFO] Riga:%s - Header inserito: %s"%(counter['tot'], number), out_file)
                   else: # stesso ordine
                       sequence += 1

                   # Inserimento dettaglio ordine  (associando la riga con l'header_id)
                   # Importazione dato: statistic.order
                   data={'name': number,
                         'partner_id': partner_id,
                         'date': order_date,
                         'deadline': order_deadline,
                         'total': total,
                         'code': articolo_id, # codice di mexal
                         'article': "%s %s"%(articolo,product_description), # descrizione articolo + descrizione italiana aggiuntiva
                         'quantity': quantity,
                         'quantity_ok': quantity_ok,
                         'total_linear_meter': total_linear_meter,
                         'total_volume': total_volume,
                         'total_weight': total_weight,
                         'note':note,                         
                         'header_id': header_id, 
                         'line_type': line_type,
                         'colli': colli,
                         'sequence': sequence,
                         }
                   
                   if not order_deadline and line_type=="a": # Comunico solo nel caso non sia riga descrittiva 
                      raise_error("[ERR] Riga:%s - Scadenza non trovata: %s"%(counter['tot'], number), out_file)
                   elif order_deadline:
                      mod_response = sock.execute(dbname, uid, pwd, 'statistic.header', 'write', header_id, {'deadline': order_deadline,}) # TODO optimize! <<<<<<<<<<<
                      

                   if type_of_line:
                      data['type']= type_of_line.lower()

                   try:
                     order_id = sock.execute(dbname, uid, pwd, 'statistic.order', 'create', data)  
                   except:
                      raise_error("[ERR] Riga:%s - Errore creando ordine: %s"%(counter['tot'], number), out_file)
                   
                   if verbose: 
                      raise_error("[INFO] Riga:%s - Ordine inserito: %s"%(counter['tot'], number), out_file)

               except:
                   raise_error("[ERR] Riga:%s - Errore di importazione: %s"%(counter['tot'],  sys.exc_info()[0]), out_file)
           else:
                   raise_error("[ERR] Riga:%s - Riga vuota o con colonne diverse: file %s, riga %s"%(counter['tot'], tot_col, len(line)), out_file)
except:
    raise_error("[ERR] Errore importando gli ordini!", out_file)
    raise 
raise_error("[INFO] Totale ordini: %s  -  Totale righe: %s"%(counter['order'],counter['tot'],), out_file)

if debug_mode: # Parte comune a tutte le procedure:
    file_log=os.path.abspath(os.path.dirname(FileInput))+"/log.FIA"
    raise_error("\n\n[DEBUG] Date files importati:", out_file)      
    i=0
    for line in open(file_log,'r'):
       i+=1
       if i>7: # jump first line (description and . / ..)
          if line and line[0:1]!=" ":
             raise_error("\tData: %s - File: %s"%(line[0:17], line[35:].strip(),), out_file)

out_file.close()           
send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)

