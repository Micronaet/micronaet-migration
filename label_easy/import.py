#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from mx.DateTime import now
from mic_ETL import *
from fiam import *

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# TODO parametrize:
taxd="20a"
taxc="20b"

header_lines=0 # non header on CSV file

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./articoli_ETL.py nome_file.csv 
         *********************
         """ 
   sys.exit()

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
bug_start_value=1.0 # for problems in pricelist starting with cost price = 0 
ID_uom_categ=getUomCateg(sock,dbname,uid,pwd,'Unit')    # Category Unit
uom_nr=getUOM(sock,dbname,uid,pwd,'PCE',{'name': 'PCE', # Create new UOM PCE
                                        'factor_inv': 1.0, 
                                        'rounding': 1.0, 
                                        'uom_type': 'reference', 
                                        'factor': 1.0, 
                                        'active': True, 
                                        'category_id': ID_uom_categ,
                                        })

#  Pricelist
pl_pricelist=[0,0,0,0,0,0,0,0,0,]   # Pricelist for Mexal 4 pricelist  ex. 0,0,0,0,
pl_fiam=[0,0,0,0,0,0,0,0,0,]         # Version of price list (Mexal 4 pricelist) ex 0,0,0,0,
CreateAllPricelist(sock, dbname, uid, pwd, ('1', '4', '5', '9','2','3','6','7','8',), ('EUR','EUR','CHF','EUR','EUR','EUR','EUR','EUR','EUR',), pl_pricelist, pl_fiam)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)
errori_iva=[]

if not (iva_credito and iva_debito):
   print "[ERROR] Non è stata trovata l'IVA credito o debito da applicare:", data
error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               '''FIELDS: warranty ean13 supply_method uos_id list_price weight track_production incoming_qty standard_price variants active price_extra mes_type
               uom_id code description_purchase default_code type name_template property_account_income qty_available location_id id uos_coeff 
               property_stock_procurement virtual_available sale_ok purchase_ok product_manager track_outgoing company_id name product_tmpl_id state
               loc_rack uom_po_id pricelist_id price_margin property_stock_account_input description
               valuation price property_stock_production seller_qty supplier_taxes_id volume outgoing_qty loc_row
               description_sale procure_method property_stock_inventory cost_method 
               partner_ref track_incoming seller_delay weight_net packaging seller_id sale_delay loc_case property_stock_account_output
               property_account_expense categ_id lst_price taxes_id produce_delay seller_ids rental
               '''
               price=[0.0,0.0,0.0,0.0,]
               csv_id=0
               ref = Prepare(line[csv_id])
               csv_id+=1
               name = Prepare(line[csv_id]).title()
               csv_id+=1
               uom = Prepare(line[csv_id]).title()
               csv_id+=1
               taxes_id = Prepare(line[csv_id])
               csv_id+=1
               ref2 = Prepare(line[csv_id]) # TODO where put it?
               csv_id+=1
               lot = Prepare(line[csv_id])  # Piece x box
               csv_id+=1
               price[0] = PrepareFloat(line[csv_id])   # Price pricelist 1 EUR
               csv_id+=1
               price[1] = PrepareFloat(line[csv_id])   # Price pricelist 4 EUR
               csv_id+=1
               price[2] = PrepareFloat(line[csv_id])   # Price pricelist 5 CHF
               csv_id+=1
               price[3] = PrepareFloat(line[csv_id])   # Price pricelist 9 EUR
               csv_id+=1
               # Calculated field:
               #import pdb; pdb.set_trace()
               if type(lot) != type(1):
                  lot=0   # in case lot doesn't contain int values 
               name="[" + (ref.replace(' ','')[0:6]) + "] " + name
                 
               data={'name': name,
                     'mexal_id': ref,
                     'import': True,
                     'sale_ok':True,
                     'purchase_ok': True,
                     'default_code': ref,
                     'uom_id': uom_nr,           # TODO test if it is NR
                     'uom_po_id': uom_nr,        # TODO test if it is NR
                     'type': 'product',          # TODO parametrize: product consu service
                     'supply_method': 'produce', # TODO parametrize: produce buy
                     'standard_price': bug_start_value,
                     'list_price': 0.0,
                     'procure_method': 'make_to_order', 
                     'q_x_pack': lot,
                     #'description': description,
                     #'description_sale'
                     #'description_spurchase'
                     #'lst_price' 
                     #'seller_qty'   
                    }
               #import pdb; pdb.set_trace()
               if taxes_id and taxes_id=='20':
                  data['taxes_id']= [(6,0,[iva_debito])]
                  data['supplier_taxes_id']= [(6,0,[iva_credito])]
               else:
                  errori_iva.append("articolo: %s" % (name))                                       
 
               # PRODUCT CREATION ***************
               error="Searching product with ref"
               item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)])
               if item: # update
                  try:
                      modify_id = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data)
                      product_id=item[0]
                  except:
                      print "[ERROR] Modify product, current record:", data
                      raise 
                  print "[INFO]", counter['tot'], "Already exist: ", ref, name
               else:           
                  counter['new'] += 1  
                  error="Creating product"
                  try:
                      product_id=sock.execute(dbname, uid, pwd, 'product.product', 'create', data) 
                  except:
                      print "[ERROR] Create product, current record:", data
                      raise                
                  print "[INFO]",counter['tot'], "Insert: ", ref, name

               # PRICE LIST CREATION/UPDATE:               
               for j in range(0,4):
                   if price[j]: # if exist price prepare PL item                        
                      item_data={#'price_round':
                                 #'price_min_margin':
                                 #'price_discount':
                                 #'base_pricelist_id': pl_pricelist[j],  # Price list
                                 'price_version_id': pl_fiam[j],   # Price list version (4 pl) # TODO erase cost=1 PL=PL-1
                                 'sequence':10,                    # Sequence for article 4 pl (for partic is less)
                                 #'price_max_margin':
                                 #'company_id
                                 'name':'%s [%s]' % (name,ref),
                                 #'product_tmpl_id':
                                 'base': 2,    # base price (product.price.type) TODO parametrize: 1 pl 2 cost
                                 'min_quantity':1,
                                 'price_surcharge': price[j] - bug_start_value, # Recharge on used base price 
                                 #'categ_id':
                                 'product_id': product_id,
                                 }
                      item_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('price_version_id', '=', pl_fiam[j]),('product_id','=',product_id)])                
                      try:
                         if item_item: # update
                             modify_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'write', item_item, item_data)                                    
                         else:           
                             new_item_id=sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'create', item_data) 
                      except:
                          print "[ERROR] Creating / Modifying item in pricelist", item_data
                          raise 
except:
    print '>>> [ERROR] Error importing articles!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

if errori_iva:
   print errori_iva
print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
