#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules used for ETL customers/suppliers
# use: ETL.py file_csv_to_import

# Modules required:
import ConfigParser, xmlrpclib, csv

def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def PrepareDate(valore):
    if valore: # TODO test correct date format
       return valore
    else:
       return time.strftime("%d/%m/%Y")

def PrepareFloat(valore):    
    valore=valore.strip()
      
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   
       
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.gpb.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator="," #config.get('dbaccess','separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Initialize variables
FileInput="prodotti_tipologia.csv"

lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
tot=0
try:
    for line in lines:    
        rottura=Prepare(line[0]).upper()  
        cols=len(line)
        if rottura=="X":
           tipology=Prepare(line[1]).title()
           item = sock.execute(dbname, uid, pwd, 'web.tipology', 'search', [('name', '=', tipology)])
           if item:
              tipology_id = item[0]
           else:
              tipology_id = sock.execute(dbname, uid, pwd, 'web.tipology', 'create', {'name': tipology,})
           
           sottotipologie={}
           max_col = 0
           for i in range(3, cols): # TODO:corretto?
               subtipology=Prepare(line[i]).title() 
               #import pdb; pdb.set_trace()
               if max_col: # TODO scrivere meglio?               
                  pass
               else:   
                   if subtipology:
                      item = sock.execute(dbname, uid, pwd, 'web.subtipology', 'search', ["&",('name', '=', subtipology),('tipology_id','=',tipology_id)])
                      if item:
                         sottotipologie[i]= item[0] #subtipology #TODO: poi diventarà l'ID 
                      else:
                         sottotipologie[i] = sock.execute(dbname, uid, pwd, 'web.subtipology', 'create', {'name':subtipology,
                                                                                                          'tipology_id':tipology_id})
                   else:
                      max_col = i
        else:
           code = Prepare(line[2])
           subtipology_ids = []

           product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code', '=', code),])
           if product_ids:
               product_id=product_ids[0]
              
               for j in range(3, max_col):
                   campo_x=Prepare(line[j]).upper()
                   if "X"==campo_x:
                      #import pdb; pdb.set_trace()
                      subtipology_ids.append(sottotipologie[j])

               #import pdb; pdb.set_trace()
               modificato = sock.execute(dbname, uid, pwd, 'product.product', 'write', product_id, {
                                                                                                   'subtipology_ids': [(6, 0, subtipology_ids)],
                                                                                                   'tipology_id': tipology_id,
                                                                                                   })
           else: # cerco il prodotto e lo aggiorno avviso se manca
               print "Codice non trovato", code
except:
    print '>>> [ERROR] Error importing data!'
    import pdb; pdb.set_trace()
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "Terminato!"
