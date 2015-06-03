#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os

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
       return 0.0   # for empty values
       
# Importo i dati con Fiam nel database:
path_etl="/home/administrator/ETL/fiam/"
cfg_file=path_etl + "openerp.cfg"

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))
verbose=True

header_lines=1 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

try:
    file_csv= "camion.csv"
    lines = csv.reader(open(file_csv,'rb'),delimiter=separator)
    counter= -header_lines
    padri={}

    for line in lines:
        if counter<0:  # jump n lines of header 
           counter+=1
        else: 
            if len(line): # jump empty lines
               #Articolo;Metallo;Diametro Tubo;Dimensioni Articolo AxBxC;Dimensioni Scatola AxBxC;Pezzi per Scatola; Peso Imballo Alluminio;Pz/Cbm;Pz/Epal;Dimensioni Pallet
               counter += 1 
               ref = Prepare(line[0])
               p_x_camion = Prepare(line[1]) 
               
               data_logistic = {
                               'item_per_camion': p_x_camion,
                               }
               counter += 1  
               padri[ref]=data_logistic
    
    product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [])
    read_product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ('id', 'default_code',))
    for elemento in read_product_ids:
        if elemento['default_code']: # and len(elemento['default_code']) in (5, 3):  # Eliminare questa condizione lasciando solo la prima parte per aggiornare tutti i prodotti che esistono come 3 iniziali
           try:
               if elemento['default_code'][:3] in padri:
                  update_product = sock.execute(dbname, uid, pwd, 'product.product', 'write', elemento['id'], padri[elemento['default_code'][:3]])
                  if verbose: 
                     print "%s) %s"%(counter, elemento['default_code'])
               if len(elemento['default_code'])>=4 and elemento['default_code'][:4] in padri: # Questo aggiorna l'eventuale valore errato inserito l'if prima
                  # Caso particolare: 127S;800 
                  update_product = sock.execute(dbname, uid, pwd, 'product.product', 'write', elemento['id'], padri[elemento['default_code'][:4]])
                  if verbose: 
                     print "%s) %s"%(counter, elemento['default_code'])
                  
           except:
               print "[ERROR] Update product - current record:", elemento['default_code']
except:  
    print '>>> [ERROR] Error importing articles!'
    import pdb; pdb.set_trace()    
    raise 
    
print '[INFO] Import terminated!'

