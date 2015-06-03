#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb

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

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./esistenze.py esistoerprogr    (per FIA e GPB)
         *********************
         """ 
   sys.exit()

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
debug=True

header_lines=0 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
file_fia=path_etl + sys.argv[1] + ".FIA"
file_gpb=path_etl + sys.argv[1] + ".GPB"

lines_fia = csv.reader(open(file_fia,'rb'),delimiter=separator)
lines_gpb = csv.reader(open(file_gpb,'rb'),delimiter=separator)

lista_fiam={}
lista_gpb={}

counter={'tot':-header_lines,}
for line in lines_fia:
    if counter['tot']<0:  # jump n lines of header 
       counter['tot']+=1
    else: 
       if len(line): # jump empty lines
          counter['tot']+=1 
          csv_id=0 # Codice
          ref = Prepare(line[csv_id]).upper()
          csv_id+=1 # Descrizione
          product_description = Prepare(line[csv_id]).title()
          lista_fiam[ref]=product_description

for line in lines_gpb:
    if counter['tot']<0:  # jump n lines of header 
       counter['tot']+=1
    else: 
       if len(line): # jump empty lines
          counter['tot']+=1 
          csv_id=0 # Codice
          ref = Prepare(line[csv_id]).upper()
          csv_id+=1 # Descrizione
          product_description = Prepare(line[csv_id]).title()
          lista_gpb[ref]=product_description

print "Situazione FIAM:"      
i=0        
for item in lista_fiam.keys():
    if item[:1]=="C":
       i+=1
       if item[1:] in lista_gpb:
          print "%s) Fiam [%s] %s ;GPB: [%s] %s"%(i, item, lista_fiam[item], item[1:], lista_gpb[item[1:]])
       else:
          print "%s) ** Non trovato in GPB: %s %s;"%(i, item, lista_fiam[item],)

print "Situazione GPB:"              
i=0        
for item in lista_gpb.keys():
    if item[:1]=="F":
       i+=1
       if item[1:] in lista_fiam:
          print "%s) GPB [%s] %s ;Fiam: [%s] %s"%(i, item, lista_gpb[item], item[1:], lista_fiam[item[1:]])
       else:
          print "%s) ** Non trovato in Fiam: %s %s;"%(i, item, lista_gpb[item],)

