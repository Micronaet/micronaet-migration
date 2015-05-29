#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xml.etree.ElementTree as ET
import xmlrpclib, sys, os

PHP_sock="http://192.168.100.73/fiam/xmlrpc/server.php"
sockphp = xmlrpclib.ServerProxy(PHP_sock)


tag={}   # da codice prodotto a ID K2:
tag['030TX']=2
tag['841']=69
tag['027']=3
tag['127S']=4
tag['132']=67
tag['840']=68
tag['127SB']=5
tag['145']=6
tag['127S']=77
tag['MT129SBI']=78
tag['023']=7
tag['081']=8
tag['830']=11
tag['831']=12
tag['820']=13
tag['MT145']=76
tag['206']=14
tag['005']=15
tag['800']=16
tag['330']=18
tag['336']=19
tag['335']=20
tag['361']=83
tag['337']=21
tag['341']=24
tag['070']=52
tag['127SF']=70
tag['024']=34
tag['021']=35
tag['220TX']=39
tag['350']=40
tag['901']=72
tag['031']=41
tag['022']=42
tag['025']=43
tag['150']=45
tag['550']=46
tag['900L']=47
tag['900S']=48
tag['362']=74
tag['650TX']=49
tag['322']=81
tag['300']=82
tag['750']=50
tag['035']=51
tag['161']=53
tag['162']=54
tag['163']=55
tag['164']=56
tag['165']=57
tag['166']=58
tag['028']=59
tag['036']=75
tag['SETAMIGO']=79
tag['SETMOVIDA']=80
tag['148']=60
tag['037']=61
tag['600']=62
tag['038']=63
tag['034']=71
tag['029TX']=64
tag['129D']=65
tag['090']=66
tag['129']=127
tag['029TXbix']=139

tag_k2_product_id={}
for k in tag.keys():
    tag_k2_product_id[tag[k]]=k


tag_category={}
#tag_category['Tavoli e Sedie']=8
tag_category['Arredo giardino']=2
tag_category['Interno']=3
tag_category['Campeggio']=5
tag_category['Accessori e Ricambi']=9
tag_category['Mare e piscina']=12

tag_k2_category_id={}
for k in tag_category.keys():
    tag_k2_category_id[tag_category[k]]=k

tag_prodotti=[
 {"id": 1143,"tagID": 5,"itemID": 18},
 {"id": 877,"tagID": 5,"itemID": 16},
 {"id": 1129,"tagID": 5,"itemID": 7},
 {"id": 1145,"tagID": 2,"itemID": 19},
 {"id": 17,"tagID": 2,"itemID": 33},
 {"id": 1134,"tagID": 5,"itemID": 35},
 {"id": 433,"tagID": 5,"itemID": 1},
 {"id": 432,"tagID": 4,"itemID": 1},
 {"id": 1019,"tagID": 5,"itemID": 59},
 {"id": 1007,"tagID": 3,"itemID": 5},
 {"id": 1293,"tagID": 3,"itemID": 4},
 {"id": 1003,"tagID": 5,"itemID": 3},
 {"id": 1137,"tagID": 5,"itemID": 6},
 {"id": 825,"tagID": 5,"itemID": 34},
 {"id": 1314,"tagID": 3,"itemID": 145},
 {"id": 824,"tagID": 2,"itemID": 34},
 {"id": 1186,"tagID": 3,"itemID": 11},
 {"id": 1289,"tagID": 3,"itemID": 12},
 {"id": 1111,"tagID": 5,"itemID": 45},
 {"id": 1018,"tagID": 4,"itemID": 59},
 {"id": 1000,"tagID": 3,"itemID": 2},
 {"id": 431,"tagID": 3,"itemID": 1},
 {"id": 1006,"tagID": 2,"itemID": 5},
 {"id": 1292,"tagID": 2,"itemID": 4},
 {"id": 1002,"tagID": 4,"itemID": 3},
 {"id": 900,"tagID": 3,"itemID": 58},
 {"id": 1053,"tagID": 3,"itemID": 13},
 {"id": 1189,"tagID": 5,"itemID": 14},
 {"id": 1126,"tagID": 4,"itemID": 60},
 {"id": 1110,"tagID": 4,"itemID": 45},
 {"id": 324,"tagID": 3,"itemID": 36},
 {"id": 1078,"tagID": 9,"itemID": 62},
 {"id": 1077,"tagID": 5,"itemID": 62},
 {"id": 1076,"tagID": 4,"itemID": 62},
 {"id": 1075,"tagID": 2,"itemID": 62},
 {"id": 1177,"tagID": 4,"itemID": 61},
 {"id": 1176,"tagID": 2,"itemID": 61},
 {"id": 1125,"tagID": 2,"itemID": 60},
 {"id": 1017,"tagID": 3,"itemID": 59},
 {"id": 1016,"tagID": 2,"itemID": 59},
 {"id": 899,"tagID": 3,"itemID": 57},
 {"id": 898,"tagID": 3,"itemID": 56},
 {"id": 893,"tagID": 3,"itemID": 55},
 {"id": 892,"tagID": 3,"itemID": 54},
 {"id": 897,"tagID": 3,"itemID": 53},
 {"id": 1164,"tagID": 4,"itemID": 52},
 {"id": 1163,"tagID": 2,"itemID": 52},
 {"id": 1162,"tagID": 5,"itemID": 51},
 {"id": 1161,"tagID": 4,"itemID": 51},
 {"id": 1160,"tagID": 2,"itemID": 51},
 {"id": 1166,"tagID": 4,"itemID": 50},
 {"id": 1165,"tagID": 2,"itemID": 50},
 {"id": 1070,"tagID": 9,"itemID": 49},
 {"id": 1069,"tagID": 5,"itemID": 49},
 {"id": 1068,"tagID": 4,"itemID": 49},
 {"id": 1067,"tagID": 2,"itemID": 49},
 {"id": 1114,"tagID": 3,"itemID": 48},
 {"id": 1113,"tagID": 2,"itemID": 48},
 {"id": 1115,"tagID": 2,"itemID": 47},
 {"id": 1035,"tagID": 9,"itemID": 46},
 {"id": 1034,"tagID": 4,"itemID": 46},
 {"id": 1033,"tagID": 3,"itemID": 46},
 {"id": 1032,"tagID": 2,"itemID": 46},
 {"id": 1109,"tagID": 2,"itemID": 45},
 {"id": 909,"tagID": 5,"itemID": 44},
 {"id": 908,"tagID": 4,"itemID": 44},
 {"id": 907,"tagID": 2,"itemID": 44},
 {"id": 1195,"tagID": 5,"itemID": 43},
 {"id": 1194,"tagID": 4,"itemID": 43},
 {"id": 1193,"tagID": 2,"itemID": 43},
 {"id": 1108,"tagID": 5,"itemID": 42},
 {"id": 1107,"tagID": 4,"itemID": 42},
 {"id": 1097,"tagID": 5,"itemID": 41},
 {"id": 1096,"tagID": 4,"itemID": 41},
 {"id": 1172,"tagID": 5,"itemID": 40},
 {"id": 1171,"tagID": 2,"itemID": 40},
 {"id": 1170,"tagID": 8,"itemID": 40},
 {"id": 1169,"tagID": 5,"itemID": 39},
 {"id": 1168,"tagID": 2,"itemID": 39},
 {"id": 1167,"tagID": 8,"itemID": 39},
 {"id": 322,"tagID": 2,"itemID": 38},
 {"id": 323,"tagID": 3,"itemID": 37},
 {"id": 1133,"tagID": 2,"itemID": 35},
 {"id": 531,"tagID": 5,"itemID": 31},
 {"id": 530,"tagID": 4,"itemID": 31},
 {"id": 529,"tagID": 2,"itemID": 31},
 {"id": 519,"tagID": 2,"itemID": 27},
 {"id": 518,"tagID": 8,"itemID": 27},
 {"id": 517,"tagID": 2,"itemID": 26},
 {"id": 516,"tagID": 8,"itemID": 26},
 {"id": 515,"tagID": 2,"itemID": 25},
 {"id": 514,"tagID": 8,"itemID": 25},
 {"id": 1157,"tagID": 2,"itemID": 24},
 {"id": 1156,"tagID": 8,"itemID": 24},
 {"id": 1093,"tagID": 2,"itemID": 23},
 {"id": 1092,"tagID": 8,"itemID": 23},
 {"id": 533,"tagID": 2,"itemID": 22},
 {"id": 532,"tagID": 8,"itemID": 22},
 {"id": 1041,"tagID": 2,"itemID": 21},
 {"id": 1040,"tagID": 8,"itemID": 21},
 {"id": 1147,"tagID": 2,"itemID": 20},
 {"id": 1146,"tagID": 8,"itemID": 20},
 {"id": 1144,"tagID": 8,"itemID": 19},
 {"id": 1142,"tagID": 2,"itemID": 18},
 {"id": 1141,"tagID": 8,"itemID": 18},
 {"id": 876,"tagID": 2,"itemID": 16},
 {"id": 875,"tagID": 8,"itemID": 16},
 {"id": 1192,"tagID": 5,"itemID": 15},
 {"id": 1191,"tagID": 2,"itemID": 15},
 {"id": 1190,"tagID": 8,"itemID": 15},
 {"id": 1188,"tagID": 2,"itemID": 14},
 {"id": 1187,"tagID": 8,"itemID": 14},
 {"id": 1052,"tagID": 2,"itemID": 13},
 {"id": 1051,"tagID": 8,"itemID": 13},
 {"id": 1288,"tagID": 2,"itemID": 12},
 {"id": 1287,"tagID": 8,"itemID": 12},
 {"id": 1185,"tagID": 2,"itemID": 11},
 {"id": 1184,"tagID": 8,"itemID": 11},
 {"id": 1298,"tagID": 5,"itemID": 8},
 {"id": 1297,"tagID": 2,"itemID": 8},
 {"id": 1128,"tagID": 4,"itemID": 7},
 {"id": 1127,"tagID": 2,"itemID": 7},
 {"id": 1136,"tagID": 4,"itemID": 6},
 {"id": 1135,"tagID": 2,"itemID": 6},
 {"id": 1001,"tagID": 2,"itemID": 3},
 {"id": 999,"tagID": 2,"itemID": 2},
 {"id": 430,"tagID": 2,"itemID": 1},
 {"id": 1180,"tagID": 5,"itemID": 63},
 {"id": 1179,"tagID": 4,"itemID": 63},
 {"id": 1178,"tagID": 2,"itemID": 63},
 {"id": 982,"tagID": 5,"itemID": 64},
 {"id": 981,"tagID": 4,"itemID": 64},
 {"id": 980,"tagID": 3,"itemID": 64},
 {"id": 979,"tagID": 2,"itemID": 64},
 {"id": 998,"tagID": 5,"itemID": 65},
 {"id": 997,"tagID": 4,"itemID": 65},
 {"id": 996,"tagID": 3,"itemID": 65},
 {"id": 995,"tagID": 2,"itemID": 65},
 {"id": 1313,"tagID": 2,"itemID": 145},
 {"id": 1296,"tagID": 5,"itemID": 66},
 {"id": 1295,"tagID": 3,"itemID": 66},
 {"id": 1294,"tagID": 2,"itemID": 66},
 {"id": 974,"tagID": 4,"itemID": 67},
 {"id": 973,"tagID": 2,"itemID": 67},
 {"id": 1118,"tagID": 4,"itemID": 68},
 {"id": 1117,"tagID": 3,"itemID": 68},
 {"id": 1116,"tagID": 2,"itemID": 68},
 {"id": 1121,"tagID": 4,"itemID": 69},
 {"id": 1120,"tagID": 3,"itemID": 69},
 {"id": 1119,"tagID": 2,"itemID": 69},
 {"id": 1022,"tagID": 5,"itemID": 70},
 {"id": 1021,"tagID": 4,"itemID": 70},
 {"id": 1020,"tagID": 2,"itemID": 70},
 {"id": 1301,"tagID": 12,"itemID": 71},
 {"id": 1300,"tagID": 5,"itemID": 71},
 {"id": 1299,"tagID": 2,"itemID": 71},
 {"id": 970,"tagID": 3,"itemID": 74},
 {"id": 969,"tagID": 2,"itemID": 74},
 {"id": 1175,"tagID": 8,"itemID": 81},
 {"id": 1158,"tagID": 8,"itemID": 82},
 {"id": 1197,"tagID": 8,"itemID": 83},
 {"id": 1200,"tagID": 19,"itemID": 84},
 {"id": 1201,"tagID": 24,"itemID": 85},
 {"id": 1202,"tagID": 25,"itemID": 86},
 {"id": 1203,"tagID": 25,"itemID": 87},
 {"id": 1204,"tagID": 25,"itemID": 88},
 {"id": 1205,"tagID": 25,"itemID": 89},
 {"id": 1206,"tagID": 25,"itemID": 90},
 {"id": 1207,"tagID": 25,"itemID": 91},
 {"id": 1249,"tagID": 2,"itemID": 92},
 {"id": 1209,"tagID": 29,"itemID": 93},
 {"id": 1210,"tagID": 29,"itemID": 94},
 {"id": 1211,"tagID": 29,"itemID": 95},
 {"id": 1212,"tagID": 29,"itemID": 96},
 {"id": 1213,"tagID": 29,"itemID": 97},
 {"id": 1214,"tagID": 29,"itemID": 98},
 {"id": 1215,"tagID": 29,"itemID": 99},
 {"id": 1216,"tagID": 29,"itemID": 100},
 {"id": 1217,"tagID": 29,"itemID": 101},
 {"id": 1218,"tagID": 29,"itemID": 102},
 {"id": 1219,"tagID": 29,"itemID": 103},
 {"id": 1220,"tagID": 29,"itemID": 104},
 {"id": 1221,"tagID": 29,"itemID": 105},
 {"id": 1222,"tagID": 29,"itemID": 106},
 {"id": 1223,"tagID": 29,"itemID": 107},
 {"id": 1224,"tagID": 29,"itemID": 108},
 {"id": 1225,"tagID": 29,"itemID": 109},
 {"id": 1226,"tagID": 29,"itemID": 110},
 {"id": 1227,"tagID": 29,"itemID": 111},
 {"id": 1228,"tagID": 29,"itemID": 112},
 {"id": 1229,"tagID": 29,"itemID": 113},
 {"id": 1230,"tagID": 29,"itemID": 114},
 {"id": 1231,"tagID": 29,"itemID": 115},
 {"id": 1232,"tagID": 29,"itemID": 116},
 {"id": 1233,"tagID": 29,"itemID": 117},
 {"id": 1234,"tagID": 29,"itemID": 118},
 {"id": 1235,"tagID": 29,"itemID": 119},
 {"id": 1247,"tagID": 2,"itemID": 121},
 {"id": 1282,"tagID": 2,"itemID": 123},
 {"id": 1281,"tagID": 2,"itemID": 122},
 {"id": 1267,"tagID": 2,"itemID": 124},
 {"id": 1283,"tagID": 2,"itemID": 125},
 {"id": 1284,"tagID": 2,"itemID": 126},
 {"id": 1285,"tagID": 2,"itemID": 127},
 {"id": 1271,"tagID": 2,"itemID": 128},
 {"id": 1272,"tagID": 2,"itemID": 129},
 {"id": 1286,"tagID": 2,"itemID": 130},
 {"id": 1274,"tagID": 2,"itemID": 131},
 {"id": 1275,"tagID": 2,"itemID": 132},
 {"id": 1276,"tagID": 2,"itemID": 133},
 {"id": 1277,"tagID": 2,"itemID": 134},
 {"id": 1278,"tagID": 2,"itemID": 135},
 {"id": 1279,"tagID": 2,"itemID": 136},
 {"id": 1280,"tagID": 2,"itemID": 137},
 {"id": 1312,"tagID": 8,"itemID": 145},
 {"id": 1311,"tagID": 3,"itemID": 147},
 {"id": 1310,"tagID": 2,"itemID": 147}]

dbname="FiamLug2012"
user="admin"
pwd="cgp.fmsp6"
server="localhost"
port="8069"

#context={'lang':'it_IT','tz':False} #Set up an italian context 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)



# 1. Leggo K2 prodotti per avere l'alias e raggiungere l'ID prodotto in openerp da ID prodotto di K2
# chiedo l'id K2 e ritorna il product_id di OpenERP
# product converter [K2 ITEMS]:
alias_code={}
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
          alias_code[alias]=int(item_id)





# Creo l tag=categoria per il prodotto (quelli con il filtro sul menu):
# Creo le categorie in OpenERP:
openerp_categoria_id={}
for categoria in tag_category:
    trovate_ids = sock.execute(dbname, uid, pwd, 'web.category', 'search', [('name','=',categoria)])
    if trovate_ids:
       openerp_categoria_id[categoria] = trovate_ids[0]
    else:   
       openerp_categoria_id[categoria] = sock.execute(dbname, uid, pwd, 'web.category', 'create', {'name': categoria})

item_ids = sock.execute(dbname, uid, pwd, 'web.k2.line', 'search', [])
esito = sock.execute(dbname, uid, pwd, 'web.k2.line', 'unlink', item_ids)

# Abbino il tag ai prodotti
for tag_item in tag_prodotti:
    # {"id": 1143,"tagID": 5,"itemID": 18}, 
    if tag_item["tagID"] not in tag_k2_category_id:
       print "codice non trovato:", tag_item
       continue # salto
    k2_category_name = tag_k2_category_id[tag_item["tagID"]]
    product_id=0
    if tag_item["itemID"] not in tag_k2_product_id:
       print "codice non trovato:", tag_item
       continue # salto
    code=tag_k2_product_id[tag_item["itemID"]]
    product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code','=',code)])
    if product_ids: 
       product_id=product_ids[0]    
       item_create = sock.execute(dbname, uid, pwd, 'web.k2.line', 'create', {'category_id': openerp_categoria_id[k2_category_name],
                                                                           'product_id': product_id,
                                                                           })
    else:
       print "Non trovato:", code                                                                       


# Mettere k2_all_product se categid=1 alotrimenti tenuto come 3!


# ################################ TOGLIERE ##################################
# STOP!!
print "Abbinare prima gli ID delle tipologie creati a mano in OpenERP"
import pdb; pdb.set_trace() # TENERE IL PDB!
# Abbinare prima gli ID delle tipologie creati a mano in OpenERP

'''Testi completi 	id 	name 	value 	type 	group 	published 	ordering
9 	DIMENSIONI BANCALE (AxBxC)
10 	pz/m³
11 	pz/epal
8 	DIMENSIONI IMBALLO (AxBxC)
7 	DIMENSIONI ARTICOLO (AxBxC)
12 	Dimensioni articolo(AxBxC)
13 	Dimensioni imballo(AxBxC)
14 	Dimensioni bancale(AxBxC)
15 	pz/m²
16 	pz/epal

qui:
  1 |          1 | 2012-09-07 09:00:29.589584 |            |           | DIMENSIONI BANCALE (AxBxC)  |        1
  2 |          1 | 2012-09-07 09:00:38.110312 |            |           | pz/m³                       |        2
  3 |          1 | 2012-09-07 09:00:47.029883 |            |           | pz/epal                     |        3
  4 |          1 | 2012-09-07 09:00:55.420271 |            |           | DIMENSIONI IMBALLO (AxBxC)  |        4
  5 |          1 | 2012-09-07 09:01:04.653782 |            |           | DIMENSIONI ARTICOLO (AxBxC) |        5

'''
convert_k2_2_oerp_id={} # ID K2 = ID openerp
convert_k2_2_oerp_id['9']=1   #bancale
convert_k2_2_oerp_id['10']=2  #m3
convert_k2_2_oerp_id['11']=3  #epal
convert_k2_2_oerp_id['8']=4   #imballo
convert_k2_2_oerp_id['7']=5   #articolo

convert_k2_2_oerp_id['12']=5
convert_k2_2_oerp_id['13']=4
convert_k2_2_oerp_id['14']=1
convert_k2_2_oerp_id['15']=2
convert_k2_2_oerp_id['16']=3

convert_k2_2_oerp_id[9]=1   #bancale
convert_k2_2_oerp_id[10]=2  #m3
convert_k2_2_oerp_id[11]=3  #epal
convert_k2_2_oerp_id[8]=4   #imballo
convert_k2_2_oerp_id[7]=5   #articolo

convert_k2_2_oerp_id[12]=5
convert_k2_2_oerp_id[13]=4
convert_k2_2_oerp_id[14]=1
convert_k2_2_oerp_id[15]=2
convert_k2_2_oerp_id[16]=3

st_ids = sock.execute(dbname, uid, pwd, 'web.k2.subtipology', 'search', [])
st_unlink = sock.execute(dbname, uid, pwd, 'web.k2.subtipology', 'unlink', st_ids)

product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('web','=',True)])                 
for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ['k2_extra_fields', 'id', 'default_code']):
    # loop for extra fields:
    extra_field=product['k2_extra_fields']    
    if extra_field:
        x_list=eval(extra_field.replace("&quot;","'"))
        # [{'id':'7','value':'59x88x162'},{'id':'8','value':'61x78x29'},{'id':'9','value':'80x227hx120'},{'id':'10','value':'7'},{'id':'11','value':'14'}]
        print "Fatto:", product['default_code']                                                                
        for item in x_list:
            if item['id'] in convert_k2_2_oerp_id and item['value'].strip(): # esiste il valore
                tipology_id = convert_k2_2_oerp_id[item['id']]
                tipology_value=item['value']
                st_ids = sock.execute(dbname, uid, pwd, 'web.k2.subtipology', 'create', {
                                                                              'product_id': product['id'],
                                                                              'tipology_id': tipology_id,                                                                            
                                                                              'name': tipology_value, # value
                                                                              })                 
            else:
                print "Non trovato", item

# ################################ TOGLIERRE ##################################

code=[]
product_item_id={}
product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code','!=',False)])                 
for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ['default_code', 'id']):
    #code.append(product['default_code'])
    product_item_id[product['default_code']]=product['id']


#for v in alias.values():
#    if v in code:
#       print "OK: '%s'"%(v)
#    else:
#       print "[ERR] KO '%s'"%(v)
    
#code_list={}
#product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code','!=',False)])                 
#for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ['default_code']):
#    sku_code = "-".join([c for c in product['default_code'].split(" ") if c]).lower()
#    if sku_code in code_list:
#       print "[ERR] Already exist:", sku_code, "Actual", product['default_code'], "Previous", code_list[sku_code]
#    else:   
#       code_list[sku_code] = product['default_code']
       #print "[INFO] SKU", sku_code, "Product", product['default_code']  


tree = ET.parse('joomla_fiam.xml')
root = tree.getroot()
#table_search=["jos_vm_product", "jos_k2_items"]
table = "jos_k2_items"

#print "DB Name:", root.attrib['name'] 
#print "TABLE: ", table, "#"*40
image_type=["Generic","L","M","S","XL","XS"]
for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       title = trash = sku = published = item_id = catid = introtext = fulltext = gallery = extra_fields = extra_fields_search  = image_caption = params = ""
       ordering=0
       for column in child:       
           if column.attrib['name']=="title":
               title=column.text 
           if column.attrib['name']=="trash":
               trash=column.text 
           if column.attrib['name']=="alias":
               sku=column.text 
           if column.attrib['name']=="published":
               published=column.text
           if column.attrib['name']=="id":
               item_id=column.text               
           if column.attrib['name']=="catid": # TODO Piazzare!!!
               catid=column.text 
           if column.attrib['name']=="introtext":
               introtext=column.text 
           if column.attrib['name']=="fulltext":
               fulltext=column.text 
           #if column.attrib['name']=="video":
           #    video=column.text 
           if column.attrib['name']=="gallery":
               gallery=column.text 
           if column.attrib['name']=="extra_fields":
               extra_fields=column.text 
           if column.attrib['name']=="extra_fields_search":
               extra_fields_search=column.text 
           if column.attrib['name']=="ordering":
               ordering=int(column.text or 0)
           #if column.attrib['name']=="featured":
           #    featured=column.text 
           #if column.attrib['name']=="featured_ordering":
           #    featured_ordering=column.text 
           if column.attrib['name']=="image_caption":
               image_caption=column.text 
           #if column.attrib['name']=="image_credits":
           #    image_credits=column.text 
           #if column.attrib['name']=="video_caption":
           #    video_caption=column.text 
           #if column.attrib['name']=="video_credits":
           #    video_credits=column.text 
           if column.attrib['name']=="params":
               params=column.text 
             
       if published == "1" and not trash == "1":           
          product_id=product_item_id[sku]
          product_modify = sock.execute(dbname, uid, pwd, 'product.product', 'write', product_id, {'vm_name':title,
                                                                                                   #'vm_short':,
                                                                                                   #'vm_description':,
                                                                                                   'k2_image_caption': image_caption,
                                                                                                   'k2_gallery': gallery,
                                                                                                   'k2_params': params,
                                                                                                   'k2_extra_fields': extra_fields,
                                                                                                   'k2_extra_field_search': extra_fields_search,
                                                                                                   'k2_ordering': ordering,
                                                                                                   'k2_introtext': introtext,
                                                                                                   'k2_fulltext': fulltext,
                                                                                                   'k2_alias': sku,
                                                                                                   'k2_all_product': catid=="1",
                                                                                                   # catid
                                                                                                   # alias
                                                                                                   })                 

          # IMMAGINI:
          if sku:
              update_id=product_item_id[sku]
              sock.execute(dbname, uid, pwd, 'product.product', 'write', update_id, {'web':True})
              hash_image=sockphp.openerp.getImageMD5(sku)
              try:             
                  os.rename("/home/administrator/photo/FiamLug2012/product/k2/%s.jpg"%(hash_image), "/home/administrator/photo/FiamLug2012/product/k2/src/%s.jpg"%(sku))
                  print "rename: k2/%s.jpg"%(hash_image),"k2/srv/%s.jpg"%(sku)
              except:
                  pass #print "[ERR] rename: /home/administrator/photo/FiamLug2012/product/k2/%s.jpg"%(conver_image[c]),"k2/srv/%s.jpg"%(c)
              for t in image_type:
                  try:             
                      os.rename("/home/administrator/photo/FiamLug2012/product/k2/%s_%s.jpg"%(hash_image,t), "/home/administrator/photo/FiamLug2012/product/k2/%s/%s.jpg"%(t,sku))
                  except:
                      print "[ERR] rename: /home/administrator/photo/FiamLug2012/product/k2/%s_%s.jpg"%(hash_image,t), " to /home/administrator/photo/FiamLug2012/product/k2/%s/%s.jpg"%(t,sku)
                    
                             


sys.exit() # spostato prima questa parte:

st_ids = sock.execute(dbname, uid, pwd, 'web.k2.subtipology', 'search', [])
st_unlink = sock.execute(dbname, uid, pwd, 'web.k2.subtipology', 'unlink', st_ids)


product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('web','=',True)])                 
for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ['k2_extra_fields', 'id', 'default_code']):
    # loop for extra fields:
    extra_field=product['k2_extra_fields']    
    #import pdb; pdb.set_trace()
    if extra_field:
        x_list=eval(extra_field.replace("&quot;","'"))
        # [{'id':'7','value':'59x88x162'},{'id':'8','value':'61x78x29'},{'id':'9','value':'80x227hx120'},{'id':'10','value':'7'},{'id':'11','value':'14'}]
        # tipology_value=""    
        print "Fatto:", product['default_code']                                                                
        for item in x_list:
            if item['id'] in convert_k2_2_oerp_id:
                tipology_id = convert_k2_2_oerp_id[item['id']]
                tipology_value=item['value']
                st_ids = sock.execute(dbname, uid, pwd, 'web.k2.subtipology', 'create', {
                                                                                'product_id': product['id'],
                                                                                'tipology_id': tipology_id,                                                                            
                                                                                'name': tipology_value, # value
                                                                                })                 
            else:
                print "Non trovato",item['id']                                           
                                                                                


