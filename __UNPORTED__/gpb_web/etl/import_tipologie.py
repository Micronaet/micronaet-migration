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
FileInput="tipologie.csv"

lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
tot=0
try:
    for line in lines:
        if len(line): 
            tot += 1  

            tipology= Prepare(line[0]).title()
            subtipology=Prepare(line[1]).title()
            item = sock.execute(dbname, uid, pwd, 'web.tipology', 'search', [('name', '=', tipology)])
            if item:
               tipology_id=item[0]
            else:   
               tipology_id = sock.execute(dbname, uid, pwd, 'web.tipology', 'create', {'name':tipology,})
            
            item = sock.execute(dbname, uid, pwd, 'web.subtipology', 'search', ["&",('name', '=', subtipology),('tipology_id','=',tipology_id)])
            if not item and subtipology: # se non c'è ed esiste il nome 
               subtipology_id = sock.execute(dbname, uid, pwd, 'web.subtipology', 'create', {'name':subtipology, 'tipology_id': tipology_id,})
            
except:
    print '>>> [ERROR] Error importing data!'
    import pdb; pdb.set_trace()
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Total line: ",tot
