#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xml.etree.ElementTree as ET
import xmlrpclib, sys, os

dbname="FiamLug2012"
user="admin"
pwd="cgp.fmsp6"
server="localhost"
port="8069"

def get_product_id_from_code(sock, dbname, uid, pwd, code):
    ''' Funzione che ritorna l'id prodotto dal codice
    '''
    item_ids=sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code', '=', code)])
    if item_ids:
       return item_ids[0]
    else:
       return False   

#context={'lang':'it_IT','tz':False} #Set up an italian context 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# 1. Leggo K2 prodotti per avere l'alias e raggiungere l'ID prodotto in openerp da ID prodotto di K2
# chiedo l'id K2 e ritorna il product_id di OpenERP
# product converter [K2 ITEMS]:
product_oerp_k2={}
tree = ET.parse('jos_k2_items.xml')
root = tree.getroot()
table = "jos_k2_items"
for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       item_id = 0
       alias = published = ""

       for column in child:       
           if column.attrib['name']=="id":
               item_id=column.text 
           if column.attrib['name']=="alias":
               alias=column.text 
           if column.attrib['name']=="published":
               published=column.text 
               
       if published == "1":           
          product_id = get_product_id_from_code(sock, dbname, uid, pwd, alias)
          if not product_id:
             print "Non trovato prodotto con codice:", alias
          else:   
             print "Trovato prodotto:", item_id, ">", alias, ">", product_id
             product_oerp_k2[int(item_id)]=product_id 

print product_oerp_k2
# 2. Leggo tutti i menuitems cercando di individuare l'ID prodotto K2
#    usato a ricavare il product_id di openERP partendo dall'ID menuitem di K2
# product menu converter  [MENU]:
product_menu_k2_product={}
tree = ET.parse('jos_menu.xml')
root = tree.getroot()
table = "jos_menu"
left_part="index.php?option=com_k2&view=item&layout=item&id="
for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       item_id = 0
       link = published = ""

       for column in child:       
           if column.attrib['name']=="id":
               item_id = column.text 
           if column.attrib['name']=="link":
               link = column.text 
           if column.attrib['name']=="published":
               published=column.text 
               
       if published == "1" and link and link[:len(left_part)]==left_part:         
          k2_product_id = int(link[len(left_part)-len(link):])
          # TODO controllare prima se esiste
          if k2_product_id in product_oerp_k2:
             product_menu_k2_product[int(item_id)] = product_oerp_k2[k2_product_id]
             print "ID menuitem K2:", item_id, " > ID product K2:", k2_product_id, product_oerp_k2[k2_product_id]
          else:
             print "Non trovato ID prodotto K2:", k2_product_id   

print product_menu_k2_product

# 3. Leggo tutti i custom modules di OpenERP, salvo l'id di openerp partendo da 
#     Pasdando il codice modulo di K2 ritorna il codice modulo in OpenERP
# custom mod openerp converter:
custom_k2_oerp={}
custom_ids = sock.execute(dbname, uid, pwd, 'web.k2.mod.custom', 'search', [])
custom_read = sock.execute(dbname, uid, pwd, 'web.k2.mod.custom', 'read', custom_ids)
for custom in custom_read:
    custom_k2_oerp[custom['k2_id']]=custom['id']
print custom_k2_oerp
# 3a. Leggo tutte le gallery (modules) di OpenERP, salvo l'id di openerp partendo da 
#     Passando il codice gallerya di K2 ritorna il codice gallery in OpenERP
# gallery openerp converter:
gallery_k2_oerp={}
gallery_ids = sock.execute(dbname, uid, pwd, 'web.k2.gallery', 'search', [])
gallery_read = sock.execute(dbname, uid, pwd, 'web.k2.gallery', 'read', gallery_ids)
for gallery in gallery_read:
    gallery_k2_oerp[gallery['k2_id']]=gallery['id']
print gallery_k2_oerp

# 4. Leggo tutti gli abbinamenti menù item con moduli K2
#    ricavo quale moduleid corrisponde in OpenERP
#    ricavo quale product_id corrisponde
#    mi creo la lista per tutti i product_id dei module_id di openerp (poi la salvo)
# product menu converter    [MODULES MENU]:
tree = ET.parse('jos_modules_menu.xml')
root = tree.getroot()
table = "jos_modules_menu"
modifiche={}
for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       moduleid = menuid = published = ""

       for column in child:       
           if column.attrib['name']=="moduleid":
               moduleid = int(column.text or 0)
           if column.attrib['name']=="menuid":
               menuid = int(column.text or 0)
               
       if moduleid in custom_k2_oerp and menuid in product_menu_k2_product:  # create modules associated:  (devono essere preimportati, qui aggiorno solamente)
          custom_id = custom_k2_oerp[moduleid]          
          product_id = product_menu_k2_product[menuid]
          if product_id in modifiche:
             modifiche[product_id].append(custom_id)
          else:
             modifiche[product_id]=[]
             modifiche[product_id].append(custom_id)
                             
#import pdb; pdb.set_trace()
#Ciclo per aggiornare tutte gli articoli custom abbinati ai prodotti:                             
for key in modifiche.keys():
    try: 
       custom_esito = sock.execute(dbname, uid, pwd, 'product.product', 'write', key, {'k2_mod_custom_ids':[(6,0,modifiche[key])]})
    except:
       print "Errore: ", key, modifiche[key]        







# 5. Leggo tutti gli abbinamenti: moduleid - itemid per vedere di creare le gallery
#    ricavo il moudleid=gallery in Openerp gallery
#    ricavo quale product_id corrisponde dal menu id
tree = ET.parse('jos_modules_menu.xml')
root = tree.getroot()
table = "jos_modules_menu"
modifiche={}
for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       moduleid = menuid = published = ""

       for column in child:       
           if column.attrib['name']=="moduleid":
               moduleid = int(column.text or 0)
           if column.attrib['name']=="menuid":
               menuid = int(column.text or 0)
               
       if moduleid in gallery_k2_oerp and menuid in product_menu_k2_product:  # create modules associated:  (devono essere preimportati, qui aggiorno solamente)
          custom_id = gallery_k2_oerp[moduleid]          
          product_id = product_menu_k2_product[menuid]
          if product_id in modifiche:
             modifiche[product_id].append(custom_id)
          else:
             modifiche[product_id]=[]
             modifiche[product_id].append(custom_id)

print modifiche
for key in modifiche.keys():
    try: 
       custom_esito = sock.execute(dbname, uid, pwd, 'product.product', 'write', key, {'k2_gallery_id':modifiche[key][0]})
    except:
       print "Errore: ", key, modifiche[key]        

