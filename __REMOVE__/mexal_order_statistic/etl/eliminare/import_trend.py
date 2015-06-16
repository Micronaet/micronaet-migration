#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ETL. import csv file with preformatted data comes from Mexal orders
# use: import.csv mexal_file_csv.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser

# Start main code *************************************************************
if len(sys.argv)!=3 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import_trend.py trendoerp1.csv [S|N] #trendoerp2.csv
         *********************
         """ 
   sys.exit()

elimino=(sys.argv[2].lower()=="s") # Elimino la prima importazione

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

header_lines = 0 # mai da mexal
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

# Elimino tutti gli elementi della tabella prima di procedere all'importazione:
if elimino:
   order_ids = sock.execute(dbname, uid, pwd, 'statistic.trend', 'search', []) 
   response =  sock.execute(dbname, uid, pwd, 'statistic.trend', 'unlink', order_ids) 

# Carico gli elementi da file CSV:
tot_col=0
try:
    for line in lines:
        if tot_col==0: # memorizzo il numero colonne la prima volta
           tot_col=len(line)
           print "[INFO] Colonne rilevate", tot_col
        if counter['tot']<0:  # salto le N righe di intestazione
           counter['tot']+=1
        else:   
           if len(line) and (tot_col==len(line)): # salto le righe vuote e le righe con colonne diverse
               counter['tot']+=1 
               try:
                   csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                   mexal_id = prepare(line[csv_id])
                   csv_id+=1      # Quantity
                   total = prepare_float(line[csv_id]) 
                   
                   # Calculated field:
                   partner_id = get_partner_id(sock, uid, pwd, mexal_id)
                   if not partner_id:
                      print "[ERR] Riga:", counter['tot'], "Partner non trovato:", mexal_id
                   
                   # Importazione dato: statistic.order
                   #import pdb; pdb.set_trace()
                   data={'name': "cliente: %d"%(partner_id,), #"%s [%d €]" % (number, total) ,
                         'partner_id': partner_id,
                         }
                   if elimino:
                      data['total']= total                      
                   else:   
                      data['total_last']= total
                
                   try:
                      trend_id = sock.execute(dbname, uid, pwd, 'statistic.trend', 'search', [('partner_id', '=', partner_id)])
                      if not trend_id:
                         trend_id = sock.execute(dbname, uid, pwd, 'statistic.trend', 'create', data)
                      else:
                         trend_id = sock.execute(dbname, uid, pwd, 'statistic.trend', 'write', trend_id, data)
                   except:
                      print "[ERR] Riga:", counter['tot'], "Errore creando ordine:", partner_id
                   if verbose: 
                      print "[INFO] Riga:", counter['tot'], "Ordine inserito:",  partner_id
                         
               except:
                   print "[ERR] Riga:", counter['tot'], "Errore di importazione:", sys.exc_info()[0]
           else:
               print "[ERR] Riga:", counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)
except:
    print '>>> [ERR] Errore importando gli ordini!'
    raise 
print "Importazione terminata! Totale ordini %s" %(counter['tot'],)
