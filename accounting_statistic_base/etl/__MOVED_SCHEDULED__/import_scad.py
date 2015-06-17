#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ETL. import csv file with preformatted data comes from Mexal orders
# use: import.csv mexal_file_csv.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser
import datetime
from posta import *
import sys, time, os # for get date of file

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import.py file_to_import.csv
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
        return: ID partner, Name partner
    '''
    if mexal_id[:2] == '06': # cliente
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', mexal_id)]) # mexal_c
    elif mexal_id[:2] == '20': # 20 fornitore                      
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', ['|', ('ref', '=', mexal_id), ('mexal_s', '=', mexal_id)])
    else: # ne cliente ne fornitore
       print "[ERR] Non trovato questo codice:", mexal_id
       return False, "Non trovato"

    if item_id:
       item_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', item_id[0],)
       return item_id[0], item_read['name']
    return False, "Non trovato"

def get_partner_info(sock, uid, pwd, partner_id):
    ''' Legge il partner e ritorna i dati relativi a:
        valore scoperto
    '''
    if partner_id:
       partner_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id) 
       if partner_read['fido_ko']: # Fido non concesso
          return -(partner_read['saldo_c'] or 0.0) -(partner_read['ddt_e_oc_c'] or 0.0)    
       else:
          return (partner_read['fido_total'] or 0.0) - (partner_read['saldo_c'] or 0.0) - (partner_read['ddt_e_oc_c'] or 0.0)
    else:
       return 0.0

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
smtp_subject = config.get('smtp', 'subject') + " (Importazione Scadenze)"
smtp_text = config.get('smtp', 'text')
smtp_log = config.get('smtp', 'log_file') + ".scadenze.csv"
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

# Elimino tutti gli elementi della tabella prima di procedere all'importazione:
deadline_ids = sock.execute(dbname, uid, pwd, 'statistic.deadline', 'search', []) 
response =  sock.execute(dbname, uid, pwd, 'statistic.deadline', 'unlink', deadline_ids) 

# Carico gli elementi da file CSV:
tot_col=0
saldo_contabile={}
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
                   csv_id+=1      # Data: YYYYMMDD
                   deadline = prepare_date(line[csv_id])
                   csv_id+=1      # Importo
                   total = prepare_float(line[csv_id]) 
                   csv_id+=1      # Tipo
                   type_id = prepare(line[csv_id]).lower()
                   
                   if mexal_id[:2]=="20": # Fornitore  (per i clienti va già bene)
                      c_o_s="s"
                      commento="Fornitore"
                      total=-total
                   else:   
                      c_o_s="c"
                      commento="Cliente"
                      
                   # Calculated field:                   
                   if total>0:
                      total_in=total
                      total_out=0.0
                   else:
                      total_in=0.0
                      total_out=-total

                   if mexal_id in saldo_contabile:
                      saldo_contabile[mexal_id]+=total
                   else:
                      saldo_contabile[mexal_id]=total

                   partner_id, partner_name = get_partner_id(sock, uid, pwd, mexal_id)
                   if not partner_id:
                      raise_error("[ERR] Riga:%s - Partner non trovato, codice Mexal: %s"%(counter['tot'], mexal_id), out_file)
                   scoperto_c = get_partner_info(sock, uid, pwd, partner_id) # TODO solo per i clienti (fare fornitori)
                   
                   # Attualizzo ad oggi la data scadenza:
                   #if deadline < datetime.date.today().strftime("%Y/%m/%d"):  # se è scaduto metto la data a ieri
                   #   deadline_real = deadline
                   #   actualized = True
                   #   deadline = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y/%m/%d")
                   #else: 
                   #   deadline_real = False
                   #   actualized = False   
                      
                   
                   # Importazione dato: statistic.order
                   #"%s/%s/%s"%(deadline[5:7],deadline[9:10],deadline[:4])
                   name = "%s [%s]: %s (%s EUR)"%(partner_name, mexal_id, deadline, total)
                   data={'name': name,
                         'partner_id': partner_id,
                         'deadline': deadline,
                         #'deadline_real': deadline_real,
                         #'actualized': actualized,
                         'total': total,
                         'in': total_in,
                         'out': total_out,
                         'type': type_id,
                         'c_o_s': c_o_s, 
                         }
                   if c_o_s == "c":
                      data['scoperto_c']= scoperto_c
                      
                   try:
                      deadline_id = sock.execute(dbname, uid, pwd, 'statistic.deadline', 'create', data)
                   except:
                      raise_error("[ERR] Riga:%s - Errore creando scadenza: %s (%s)"%(counter['tot'], deadline, name), out_file)
                   if verbose: 
                      raise_error("[ERR] Riga:%s - Scadenza inserita: %s"%(counter['tot'], deadline), out_file)
                             
               except:
                   raise_error("[ERR] Riga:%s - Errore di importazione: %s"%(counter['tot'], sys.exc_info()[0]), out_file)
           else:
               print "[ERR] Riga:", counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)               
               raise_error("[ERR] Riga:%s - Riga vuota o con colonne diverse: rilevate inizio: %s, ora: %s"%(counter['tot'], tot_col, len(line)), out_file)
except:
    raise_error("[ERR] Errore importando gli deadline!", out_file)
    raise 
    
# Messo i saldi contabili nelle schede cliente (interessano solo per i pagamenti):
#import pdb; pdb.set_trace()
print ">>>>> Aggiornamento saldi partner!"
for mexal_id in saldo_contabile.keys():
    if mexal_id[:2] in ('06', '20'): # cliente o fornitore
       if mexal_id[:2] == '06':
          cof='c'
       else:
          cof='s'   
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_' + cof, '=', mexal_id)]) 
       if item_id:
           mod_id = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item_id, {'saldo_' + cof: saldo_contabile[mexal_id]})
       else:
          raise_error("[ERR] Non trovato: %s"%(mexal_id,), out_file)
    else:
        raise_error("[ERR] Non e' ne cliente ne fornitore: %s"%(mexal_id,), out_file)

raise_error("Totale scadenze: %s"%(counter['tot'],), out_file)

out_file.close()           
send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)

