#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ETL. import csv file with preformatted data comes from Mexal orders
# use: import.csv mexal_file_csv.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser, datetime
from posta import *
import sys, time, os # for get date of file

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import_product.py fatmesartoerp.FIA
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

def get_partner_name(sock, uid, pwd, partner_id):
    ''' Ricavo il nome del partner
    '''
    partner_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id)
    if partner_read:
       return partner_read['name']
    return ''

FileInput = sys.argv[1]
if FileInput:
   sigla_azienda = FileInput[-3:].lower()
else:
   print "[ERR] File input non presente!"
   sys.exit()   
if sigla_azienda in ('gpb','fia'):
   cfg_file = os.path.join(os.path.expanduser("~"), "etl", "fiam", sigla_azienda + ".openerp.cfg")
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

verbose=False # TODO togliere
debug=True # TODO togliere

smtp_sender = config.get('smtp', 'sender')
smtp_receiver = config.get('smtp', 'receiver')
smtp_subject = config.get('smtp', 'subject') + " (Importazione Fatturato prodotti)"
smtp_text = config.get('smtp', 'text')
smtp_log = config.get('smtp', 'log_file') + ".prodotti.csv"
smtp_server = config.get('smtp', 'server')
#verbose_mail: True

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
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

# Elimino tutto
errore_da_comunicare=False
print "*** Elimino vecchio archivio invoice!"
invoice_item_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'search', [])
result_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'unlink', invoice_item_ids)

print "*** Inizio importazione"
# Carico gli elementi da file CSV:
tot_col=0
totale_stagione=[0,0,0]   # -2, -1, attuale
fatturato_elementi={}
try:
    for line in lines:
        if tot_col==0: # memorizzo il numero colonne la prima volta
           tot_col=len(line)
           print "*** Colonne rilevate", tot_col
           raise_error("[INFO] Procedura: %s \n\tFile importato: %s [creazione: %s]"%(sys.argv, FileInput, create_date), out_file)
        if counter['tot']<0:  # salto le N righe di intestazione
           counter['tot']+=1
        else:   
           if (len(line) and (tot_col==len(line))): #or (len(line)==5): # salto le righe vuote e le righe con colonne diverse
               counter['tot']+=1 
               try:
                   csv_id=0       # Famiglia
                   name = prepare(line[csv_id])
                   csv_id+=1      # Mese
                   month = int(prepare(line[csv_id]) or 0 )
                   csv_id+=1      # Anno
                   year = prepare(line[csv_id])
                   csv_id+=1      # Totale
                   total_invoice = prepare_float(line[csv_id]) or 0.0
                   #if len(line)==5:
                   csv_id+=1      # Tipo (OC o FT< comprende BC)
                   type_document = prepare(line[csv_id]).lower()
                   #else:
                   #   type_document = 'ft'   
                                                              
                   # Calculated field:
                   if type_document not in ('ft', 'bc', 'oc'):
                      raise_error("[ERR] Riga: %s - Tipo di documento non riconosciuto, sigla: %s"%(counter['tot'], type_document), out_file) 
                      errore_da_comunicare=True
                      type_document=False
                   data = {"name": name, 
                           "month": month, 
                           "type_document": type_document,
                          }
         
                   # Calcolo in quale anno inserire il fatturato (specchio di 3)
                   if not (year or month): 
                      raise_error("[ERR] Riga %s - Mese [%s] o anno [%s] non trovati!"%(counter['tot'], month, year), out_file) 
                      errore_da_comunicare=True

                   anno_mese = "%s%02d"%(year, month) 
                   
                   anno_attuale = int(datetime.datetime.now().strftime("%Y"))
                   mese_attuale = int(datetime.datetime.now().strftime("%m"))
                   
                   if mese_attuale >=1 and mese_attuale <=8:
                      anno_riferimento = anno_attuale - 1 # la stagione è partita l'anno scorso
                   elif mese_attuale >=9 and mese_attuale <=12:
                      anno_riferimento = anno_attuale  # la stagione è partita l'anno scorso
                   else:   
                      raise_error("[ERR] Riga: %s - Errore mese attuale"%(counter['tot']), out_file) 
                      errore_da_comunicare=True                   

                   # TODO: inserire anche gli OC ###############################
                   # Periodo settembre - anno attuale >> agosto - anno prossimo
                   if anno_mese >= "%s09"%(anno_riferimento,) and anno_mese <= "%s08"%(anno_riferimento + 1,): # current
                      data['total'] = total_invoice     # Aggiorno il record da scrivere con il totale
                      totale_stagione[2]+=total_invoice # Totalizzo i valori per stagione
                   elif anno_mese >= "%s09"%(anno_riferimento -1,) and anno_mese <= "%s08"%(anno_riferimento,): # anno -1
                      data['total_last'] = total_invoice
                      totale_stagione[1]+=total_invoice # Totalizzo i valori per stagione
                   elif anno_mese >= "%s09"%(anno_riferimento -2,) and anno_mese <= "%s08"%(anno_riferimento -1,): # anno -2
                      data['total_last_last'] = total_invoice
                      totale_stagione[0]+=total_invoice # Totalizzo i valori per stagione
                   else:  
                      raise_error("[ERR] Riga: %s - Periodo anno-mese non trovato (fuori dal range delle 3 stagioni): %s-%s"%(counter['tot'], year, month), out_file) 
                      errore_da_comunicare=True                      

                   # Sommo sul totale per elemnto   
                   if name not in fatturato_elementi:
                      fatturato_elementi[name] = 0.0 # inizializzo
                   fatturato_elementi[name] += total_invoice
                      
                   try:                      
                      invoice_id = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'create', data)
                   except:
                      raise_error("[ERR] Riga: %s - Errore creando fatturato prodotto: %s"%(counter['tot'], name), out_file) 
                      errore_da_comunicare=True                      

                   if verbose: 
                      raise_error("[ERR] Riga: %s - Fatturato prodotto inserito: %s"%(counter['tot'], name), out_file) 
               except:
                   raise_error("[ERR] Riga: %s - Errore di importazione: %s"%(counter['tot'], sys.exc_info()[0]), out_file) 
                   errore_da_comunicare=True                      
           else:
               raise_error("[ERR] Riga: %s - Riga vuota o con colonne diverse: col attuale= %s col effettive= %s"%(counter['tot'], tot_col, len(line)), out_file) 
               errore_da_comunicare=True                      
except:
    raise_error('>>> [ERR] Errore importando gli ordini!', out_file) 
    errore_da_comunicare=True                      
    raise 

raise_error("Importazione terminata! Totale elementi %s" %(counter['tot'],), out_file)
raise_error("Calcolo percentuale sul totale, Totale fatturato: anno 0: %s, anno-1: %s, anno-2, %s"%(totale_stagione[2],totale_stagione[1],totale_stagione[0]), out_file)

# Calcolo la percentuale sui 3 anni per decidere chi fare vedere:
try: 
    totale_fatturato_tre_stagioni= totale_stagione[2] + totale_stagione[1] + totale_stagione[0]

    # Remove some code:
    product_removed_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice.product.removed', 'search', [])
    product_removed = [item['name'] for item in sock.execute(dbname, uid, pwd, 'statistic.invoice.product.removed', 'read', product_removed_ids)]
    
    most_popular=[]
    for key_famiglia in fatturato_elementi.keys():
        percentuale_fatturato = fatturato_elementi[key_famiglia] / totale_fatturato_tre_stagioni
        if percentuale_fatturato >= 0.005: # 0,5% su tutte e tre le stagioni
           # Scrivo l'elemento
           if key_famiglia not in product_removed and key_famiglia not in most_popular:
              most_popular.append(key_famiglia)
        
    product_item_to_show_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'search', [('name', 'in', most_popular)])
    product_updated_percentile = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'write', product_item_to_show_ids , {'visible': True,})

    print "Applicata visibilità articoli più popolari!"

    if debug:        
       raise_error("[DEBUG] Fatturato elementi:\n%s\n"%(fatturato_elementi), out_file) 
    if debug: 
       raise_error("[DEBUG] Visibili:\n%s\n"%(most_popular), out_file) 
    if debug: 
       raise_error("[DEBUG] Fatturato stagioni:\n0: %s\t1: %s\t2: %s\t[ Totale: %s ]\n"%(totale_stagione[2],totale_stagione[1],totale_stagione[0],sum(totale_stagione)), out_file) 
       
    out_file.close()           
except:
    raise_error("[ERR] Calcolando i più popolari da fare vedere", out_file) 
    errore_da_comunicare=True

if errore_da_comunicare or datetime.date.today().weekday()==0: # C'è un errore o è lunedì
   send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)

