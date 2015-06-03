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
    file_csv= "padri.csv"
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
               csv_id = 0 # Codice
               ref = Prepare(line[csv_id])
               csv_id+= 1 # Articolo
               article = Prepare(line[csv_id]).title()
               csv_id+= 1 # Metallo
               metal = Prepare(line[csv_id]).upper()
               csv_id+= 1 # Diametro Tubo
               diameter = Prepare(line[csv_id]) 
               csv_id+= 1 # Dimensioni Articolo AxBxC
               dim_article = Prepare(line[csv_id])
               csv_id+= 1 # Dimensioni Scatola AxBxC
               dim_pack = Prepare(line[csv_id]) 
               csv_id+= 1 # Pezzi per Scatola
               p_x_pack = Prepare(line[csv_id]) 
               csv_id+= 1 # Peso Imballo
               weight_pack = Prepare(line[csv_id])
               csv_id+= 1 # Pz/Cbm
               p_x_mq = Prepare(line[csv_id]) 
               csv_id+= 1 # Pz/Epal
               p_x_pallet = Prepare(line[csv_id]) 
               csv_id+= 1 # Dimensioni Pallet
               pallet_dimension = Prepare(line[csv_id]) 
               # Calculated fields:
               
               # ref    article    
               data_logistic = {
                               'telaio': metal,
                               'pipe_diameter': diameter,
                               'weight_packaging': weight_pack,
                               'item_per_box': p_x_pack,
                               'item_per_pallet': p_x_pallet,
                               'item_per_mq': p_x_mq,
                               'dim_article':dim_article,
                               'dim_pack': dim_pack,
                               'dim_pallet': pallet_dimension,
                               }
               counter += 1  
               padri[ref]=data_logistic
    
    # Dopo avere letto tutta la lista aggiorno i campi con 5 articoli
    product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [])
    read_product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ('id', 'default_code',))
    for elemento in read_product_ids:
        if elemento['default_code']: # and len(elemento['default_code']) in (5, 3):  # Eliminare questa condizione lasciando solo la prima parte per aggiornare tutti i prodotti che esistono come 3 iniziali
           try:
               if elemento['default_code'][:3] in padri:
                  update_product = sock.execute(dbname, uid, pwd, 'product.product', 'write', elemento['id'], padri[elemento['default_code'][:3]])
                  if verbose: 
                     print "%s) %s"%(counter, elemento['default_code'])
           except:
               print "[ERROR] Update product - current record:", elemento['default_code']
except:  
    print '>>> [ERROR] Error importing articles!'
    import pdb; pdb.set_trace()    
    raise 
    
print '[INFO] Import terminated!'

