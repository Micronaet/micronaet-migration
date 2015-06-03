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
       
# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./esistenze.py esistoerprogr    (per FIA e GPB)
         *********************
         """ 
   sys.exit()

# Importo i dati con Fiam nel database:
path_etl=os.path.expanduser('~/ETL/fiam/')
cfg_file=path_etl + "openerp.cfg"
# Sede: cfg_file = "openerp.cfg"

   
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
dbname2=config.get('dbaccess','dbname2')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))
verbose=True

header_lines=0 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
# DB1:
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# DB2:
sock_gpb = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid_gpb = sock_gpb.login(dbname2 ,user ,pwd)
sock_gpb = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Remove all previous data:
remove_ids=sock.execute(dbname, uid, pwd, 'statistic.store', 'search', [])
removed=sock.execute(dbname, uid, pwd, 'statistic.store', 'unlink', remove_ids)

elementi={"FIA": {}, "GPB": {}}

# Load pack for product:
q_x_packs={"FIA": {}, "GPB": {}}

pack_ids=sock.execute(dbname, uid, pwd, 'product.product', 'search', [])
for item in sock.execute(dbname, uid, pwd, 'product.product', 'read', pack_ids, ('q_x_pack','default_code')):
    q_x_packs["FIA"][item['default_code']] = item['q_x_pack']
    
pack_ids = sock_gpb.execute(dbname, uid_gpb, pwd, 'product.product', 'search', [])
for item in sock_gpb.execute(dbname, uid_gpb, pwd, 'product.product', 'read', pack_ids, ('q_x_pack','default_code')):
    q_x_packs["GPB"][item['default_code']] = item['q_x_pack']

try:
    for azienda in ["FIA", "GPB"]:    
        # Open CSV passed file (see arguments) mode: read / binary, delimiation char 
        file_csv="%s%s.%s"%(path_etl, sys.argv[1], azienda)

        lines = csv.reader(open(file_csv,'rb'),delimiter=separator)
        counter={'tot':-header_lines, 'new':0} # no header lines

        try:
            for line in lines:
                if counter['tot']<0:  # jump n lines of header 
                   counter['tot']+=1
                else: 
                    if len(line): # jump empty lines
                       counter['tot']+=1 
                       csv_id = 0 # Codice
                       ref = Prepare(line[csv_id])
                       csv_id+= 1 # Descrizione
                       product_description = Prepare(line[csv_id]).title()
                       csv_id+= 1 # Unità di misura
                       product_um = Prepare(line[csv_id]).upper()
                       csv_id+= 1 # Q.tà di inventario
                       inventary = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Carico
                       value_in = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Scarico
                       value_out = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Esistenza
                       balance = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Ordini a fornitore
                       supplier_order = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Ordini cliente impegnati
                       customer_order = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Ordini cliente automatici/in produzione
                       customer_order_auto = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Ordini cliente in sospeso
                       customer_order_suspended = PrepareFloat(line[csv_id]) or 0.0
                       csv_id+= 1 # Supplier
                       supplier = Prepare(line[csv_id]).title()
                       csv_id+= 1 # Note
                       product_description += "\n" + (Prepare(line[csv_id]).title() or '')
                       csv_id+= 1 # Mexal ID supplier
                       mexal_s = Prepare(line[csv_id]) or False
                       
                       # Calculated fields:
                       company = azienda.lower()
                       disponibility = balance + supplier_order - customer_order - customer_order_suspended # E + F - I - S TODO automatici??
                       product_um2 = ""
                       inventary_last = 0.0
                       q_x_pack = q_x_packs[azienda][ref] if ref in q_x_packs[azienda] else 0
                       
                       elementi[azienda][ref] = {
                                'company': company, 
                                'supplier': supplier,
                                'mexal_s': mexal_s, 
                                'product_code': ref,
                                'product_description': product_description,
                                'product_um': product_um,
                                'q_x_pack': q_x_pack,

                                # Value fields
                                'inventary': inventary,
                                'q_in': value_in,
                                'q_out': value_out,
                                'balance': balance,
                                'supplier_order': supplier_order,
                                'customer_order': customer_order,
                                'customer_order_auto': customer_order_auto,
                                'customer_order_suspended': customer_order_suspended,

                                # Field calculated:
                                'disponibility': disponibility,
                                'product_um2': product_um2,
                                'inventary_last': inventary_last,
                                }
                        
                       # LINE CREATION ***************
                       counter['new'] += 1  
        except:
            print '>>> [ERROR] Error importing articles!'
            raise 

        # Leggo file vendite tra una ditta e l'altra (aggiorno la q_in togliendolo e la q_out sommandolo:
        file_scambio="%s%s.%s"%(path_etl, "fia-gpb", azienda)
        lines = csv.reader(open(file_scambio,'rb'), delimiter=separator)

        for line in lines:
            if len(line): # jump empty lines
               csv_id = 0 # Codice
               ref = Prepare(line[csv_id])
               csv_id+= 1 # Q. vendita
               value_sale = PrepareFloat(line[csv_id]) or 0.0
               if ref in elementi[azienda]:
                  elementi[azienda][ref]['q_in']-=value_sale
                  elementi[azienda][ref]['q_out']-=value_sale #anche se è uno scarico il numero è indicato in positivo
           
    commento=""
    for azienda in ["FIA", "GPB"]:
        if azienda == "FIA":
           altra_azienda="GPB"
        else:   
           altra_azienda="FIA"
           
        total={'jump':0,'normal':0,'double':0,'total':0}        
        for item in elementi[azienda].keys():            
            total['total']+=1
            if ((azienda=="FIA") and (item[:1]=="C") and (item[1:] in elementi["GPB"])) or ((azienda=="GPB") and (item[:1]=="F") and (item[1:] in elementi["FIA"])): # Salto gli articoli dell'altra azienda
               # Do nothing (andrà sommato con l'altra azienda)
               total['jump']+=1
               print "Riga: %s [%s] SALTATO [%s] %s"%(total['total'], azienda, item, elementi[azienda][item]['product_description'])
            elif ((azienda=="FIA") and ("F" + item in elementi["GPB"])) or ((azienda=="GPB") and ("C" + item in elementi["FIA"])): # Sommo gli articoli di questa azienda
               total['double']+=1
               if azienda=="FIA": 
                  item_other="F" + item 
               else:   
                  item_other="C" + item 
                  
               data_store={   
                       'company': elementi[azienda][item]['company'], 
                       'supplier': elementi[azienda][item]['supplier'], 
                       'product_code': elementi[azienda][item]['product_code'],
                       'product_description': elementi[azienda][item]['product_description'],
                       'product_um': elementi[azienda][item]['product_um'],

                       'inventary': elementi[azienda][item]['inventary'] + elementi[altra_azienda][item_other]['inventary'],   
                       'q_x_pack': elementi[azienda][item]['q_x_pack'],
                       'q_in': elementi[azienda][item]['q_in'] + elementi[altra_azienda][item_other]['q_in'],
                       'q_out': elementi[azienda][item]['q_out'] + elementi[altra_azienda][item_other]['q_out'],
                       'balance': elementi[azienda][item]['balance'] + elementi[altra_azienda][item_other]['balance'],
                       'supplier_order': elementi[azienda][item]['supplier_order'] + elementi[altra_azienda][item_other]['supplier_order'],
                       'customer_order': elementi[azienda][item]['customer_order'] + elementi[altra_azienda][item_other]['customer_order'],
                       'customer_order_auto': elementi[azienda][item]['customer_order_auto'] + elementi[altra_azienda][item_other]['customer_order_auto'],
                       'customer_order_suspended': elementi[azienda][item]['customer_order_suspended'] + elementi[altra_azienda][item_other]['customer_order_suspended'],

                       'disponibility': elementi[azienda][item]['disponibility']  + elementi[altra_azienda][item_other]['disponibility'],
                       'product_um2':  elementi[azienda][item]['product_um2'],
                       'inventary_last':  elementi[azienda][item]['inventary_last'],

                       'both': True, # for elements present in both company
               }
               try: 
                  store_create=sock.execute(dbname, uid, pwd, 'statistic.store', 'create', data_store) 
                  print "Riga: %s [%s] DOPPIO [%s] %s"%(total['total'], azienda, item, elementi[azienda][item]['product_description'])
               except:
                  print "[ERR] Riga: %s importando:%s"%(total['total'], elementi[azienda][item])
            else: # extra items (nessuna intersezione)
                total['normal']+=1
                store_create=sock.execute(dbname, uid, pwd, 'statistic.store', 'create', elementi[azienda][item])
                print "Riga: %s [%s] NORMALE [%s] %s"%(total['total'], azienda, item, elementi[azienda][item]['product_description'])
        commento+= "\n[%s] %s"%(azienda,total)
        print commento
except:
    print '>>> [ERROR] General Error!'
    raise 

