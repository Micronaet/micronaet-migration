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
separator=";" #config.get('dbaccess','separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Initialize variables
FileInput="prodotti_categorie.csv"

lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
tot=0
try:
    for line in lines:    
        tot+=1
        #import pdb; pdb.set_trace()
        category=Prepare(line[0]).title()
        linea=Prepare(line[1]).title()
        code=Prepare(line[2])
        #calculed:
        if category:
           category_ids = sock.execute(dbname, uid, pwd, 'web.category', 'search', [('name', '=', category)])
           if category_ids:
              category_id = category_ids[0]
           else:
              category_id = sock.execute(dbname, uid, pwd, 'web.category', 'create', {'name': category,})
        if linea:
           line_ids = sock.execute(dbname, uid, pwd, 'web.line', 'search', ["&", ('name', '=', linea), ('category_id', '=', category_id)])
           if line_ids:
              line_id = line_ids[0]
           else:
              line_id = sock.execute(dbname, uid, pwd, 'web.line', 'create', {'name': linea, 
                                                                              'category_id': category_id
                                                                              })


        product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code', '=', code),])
        if product_ids:
            product_id = product_ids[0]
            modificato = sock.execute(dbname, uid, pwd, 'product.product', 'write', product_id, {'line_id': line_id,
                                                                                                 'category_id': category_id,})
        else: # cerco il prodotto e lo aggiorno avviso se manca
            print "Codice non trovato", code
except:
    print '>>> [ERROR] Error importing data!'
    import pdb; pdb.set_trace()
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "Terminato!"
