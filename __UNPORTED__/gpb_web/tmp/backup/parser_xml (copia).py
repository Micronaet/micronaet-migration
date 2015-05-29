#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xml.etree.ElementTree as ET
import xmlrpclib, sys, os

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



alias={}
alias['movida-xl']='030TX'
alias['altea']='840' # si chiama Paola però!
alias['fiesta']='027' # 127
alias['fiesta-soft-01']='127S'
alias['wheely']='132'
alias['altea']='841' # DOPPIA con braccioli *****************************
alias['fiesta-sb']='127SB'
alias['samba']='145'  # 045
alias['cuscino-fiesta-soft']='127S'
alias['dondolina']='023' # 123
alias['spaghetti']='081'
alias['atena']='830'
alias['atena-con-braccioli']='831'
alias['mya']='820'
alias['lola']='206'
alias['regista']='005' # 205
alias['spring']='800'
alias['tavoli-sirio']='330' # 331
alias['donatello']='336'
alias['raffaello']='335'
alias['michelangelo']='337'
alias['pegaso-werzalit-70x70']='341'
alias['river']='070'
alias['fiesta-ecoleather']='127SF'  
alias['playa-cod-024-ok']='024'
alias['luna']='021'
alias['regista-woody']='220TX' # 200L   220TX   220L NC    900TX NC  ### era 200L
alias['woody']='350'  # 350NC
alias['matty']='901' # 901S, 901NC
alias['jolly']='031' # 131
alias['quick']='022'
alias['betty']='025'
alias['susy-baby-chair']='150'
alias['separè']='550'
alias['linda']='900L' # 900L NC
alias['linda-soft']='900S' # 900S NC
alias['leonardo-90x90']='360'
alias['leonardo-160/220x100']='362'            # DOPPIO  **********************************
alias['leonardo-160x90']='361'
alias['tris']='322'
alias['club']='300' # 301
alias['marea']='750'
alias['amigo']='035' # 135
alias['bitter-cod-161']='161'
alias['bitter-art-162']='162'
alias['bitter-art-163']='163'
alias['ginger-art-164']='164'
alias['ginger-art-165']='165'
alias['ginger-art-166']='166'
alias['chico']='028' #  128  128SF
alias['amigo-40+']='036'
alias['tango-contract-xl']='148'
alias['casanova']='037'
alias['amigoxxl']='038'
alias['amigo-top']='034'
alias['movida']='029TX' # anche 129TX
alias['movida-dralon']='129D' # 129DB  (DB bracciolo)
alias['amida']='090' #190
alias['129']='129'

alias['cuscino-samba--tango']='MT145' #- 148  # ID 76  ? non pubblicaot
alias['cuscino-per-movida']='MT129SBI'        # ID 78  era MT129
#alias['nuovo-articolo']=''                    # ID 144   ??? non interessa
#alias['leonardo-90x90']=''                    # ID 145   ???
alias['set-amigo']='SETAMIGO'                 # ID 79
alias['set-movida']='SETMOVIDA'               # ID 80
alias['parasole']='600'                       # ID 62   Messeo in 600 da parasole
alias['poggiatesta']='650TX'  # 651TX         # ID 49

conver_image={}
conver_image['030TX']='e0a70f72bdae9885bfc32d7cd19a26a1'
conver_image['841']='2cebfdae7a8ea5d691033c085990a9d4'
conver_image['027']='94d43e327d9303539cb1e2aac7032668'
conver_image['127S']='2ff2ba0051687eef5ca0459cf942940c'
conver_image['132']='4695cb3b19cbf906e45dac0da0913068'
conver_image['841']='deb9f9efc56ef2a940bdf0d58ccaad5c'
conver_image['127SB']='ffee2447b152494b43d9816faaea83c8'
conver_image['145']='ada9a09acea936d776a6f55c82778c43'
conver_image['127S']='d48ed900e79fa9547169c26138b4cd8d'
conver_image['MT129SBI']='13f34e2b533e12c6166f88368dcd8c07'
conver_image['023']='9caa2793658f3cc387f216157300b1ce'
conver_image['081']='184b7cb84d7b456c96a0bdfbbeaa5f14'
conver_image['830']='c82cc4e14a1d2c8c8ffff9840d24b558'
conver_image['831']='3899dfe821816fbcb3db3e3b23f81585'
conver_image['820']='48ee1e8a0a8f50dce4f8cb9ab418e211'
conver_image['MT145']='924e149af069b8ea323a809fbb1171d4'
conver_image['206']='fd8b0f77d767f1f6640afba6916ff67c'
conver_image['005']='fc1da7257992fc36032e11db3df7a664'
conver_image['800']='c9b002fe1bb0320831a8ae78670fdb6f'
conver_image['330']='4965657af186b9092c7a96976ffe881c'
conver_image['336']='f4b6dca0e2911082f0eb6e1df1a0e11d'
conver_image['335']='c889234799e865bbe90cee71f6cd2e53'
conver_image['361']='1d73e13563b8be946c0f00bab252d7ea'
conver_image['337']='9b2c4b44fb86522964124ed80d03c5e8'
conver_image['341']='233826a67be66a810b23a263230da62e'
conver_image['070']='22c02097e4438bd2f2f3fe4a6a3ab0e1'
conver_image['127SF']='3749aaa8ee129d7e919bddcc7e09cd36'
conver_image['024']='f710044bf79a4b1f5d8b085e5e5d9711'
conver_image['021']='0b1ad7a7b79268a1f4558db78e092446'
conver_image['220TX']='c99e3db826c0f4cc2688a36ce3b60e1a'
conver_image['350']='ccb4e23c8aa216f1e96d31ab209c036b'
conver_image['901']='d6086de322f98f66cc694f32ea284557'
conver_image['031']='6f43b5263fbba79c5962514b85d34738'
conver_image['022']='19f9cefdfb07230a68581d617885a3af'
conver_image['025']='8b6e33345ac8d5ffd9cf0d107a7d9e9d'
conver_image['150']='37a06e4a72d6cb27621f1ed829bbee81'
conver_image['550']='64d93d666355a43c4a86679a030d35b6'
conver_image['900L']='542390225756f78888142d54f3d17e01'
conver_image['900S']='c1572c59821062c96d0fc33ad32a2983'
conver_image['360']='5483e331a9bace540b3a2478fc014e25'
conver_image['650TX']='620466077c427f141effa294382f5fba'
conver_image['322']='267b1948fa84309bc99f9c0289cabe44'
conver_image['300']='aaa082d2257ab65aecf61c2340e9c5b9'
conver_image['750']='a522a6005d1cb428ea34ef1769cd7452'
conver_image['035']='eb6c7c01c4e98e1f2578f9959463b973'
conver_image['161']='90701d02ae3da0e5a21abbd900c25748'
conver_image['162']='a27a3b73d355048c6bab885897085f62'
conver_image['163']='220c08548cac211cc7db219bb52f46cf'
conver_image['164']='d3b3799d6611d677944f5f86a500beb3'
conver_image['165']='0548677e6432786dd8df61eb3aaec139'
conver_image['166']='954fb0ebf1d84fb921bfb0b6e045d57f'
conver_image['028']='339a0e1449b6b4062056bc300d87e893'
conver_image['036']='68b62085e41e8f225811766f8d5eb2bb'
conver_image['SETAMIGO']='deb45d333d0414ba3de42155789fdb4a'
conver_image['SETMOVIDA']='852967248dd3e6cb3942a1fe6af42945'
conver_image['148']='83c2446a0896df0a1f4af01c940ae1d9'
conver_image['037']='00d9b1e39f02d57be65ad2a9a6eaa3b8'
conver_image['600']='c3997142576e6f4d163ead570965368d'
conver_image['038']='9415f9bcd76598f9c08127db1641b596'
conver_image['034']='1698b847c2e4fe98c05adcdc9d420590'
conver_image['029TX']='e9c724eeb5636d1c1c1a2c2e85d40377'
conver_image['129D']='be28adfff47893c4519c1307dc6b8866'
conver_image['090']='4d8c9898b5bb88437f053c8b957f47f3'
conver_image['129']='9ded0288e863fbe79d863f606cb05c21'
conver_image['029TX']='7f2cd38b7681e6e2ef83b5a7a5385264'


dbname="FiamLug2012"
user="admin"
pwd="cgp.fmsp6"
server="localhost"
port="8069"

#context={'lang':'it_IT','tz':False} #Set up an italian context 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

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

import pdb; pdb.set_trace()
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
import pdb; pdb.set_trace() # TENERE IL PDB!
# Abbinare prima gli ID delle tipologie creati a mano in OpenERP

convert_k2_2_oerp_id={} # ID K2 = ID openerp
convert_k2_2_oerp_id['9']=6   #bancale
convert_k2_2_oerp_id['10']=2  #m3
convert_k2_2_oerp_id['11']=3  #epal
convert_k2_2_oerp_id['8']=4   #imballo
convert_k2_2_oerp_id['7']=5   #articolo

convert_k2_2_oerp_id['12']=5
convert_k2_2_oerp_id['13']=4
convert_k2_2_oerp_id['14']=6
convert_k2_2_oerp_id['15']=2
convert_k2_2_oerp_id['16']=3

convert_k2_2_oerp_id[9]=6   #bancale
convert_k2_2_oerp_id[10]=2  #m3
convert_k2_2_oerp_id[11]=3  #epal
convert_k2_2_oerp_id[8]=4   #imballo
convert_k2_2_oerp_id[7]=5   #articolo

convert_k2_2_oerp_id[12]=5
convert_k2_2_oerp_id[13]=4
convert_k2_2_oerp_id[14]=6
convert_k2_2_oerp_id[15]=2
convert_k2_2_oerp_id[16]=3

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
                                                                                
import pdb; pdb.set_trace()






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
          try:
              if sku!="nuovo-articolo":
                  if sku==u'separ\xe8':
                     alias_product="550"
                  else:
                     alias_product=alias[sku]

                  product_id=product_item_id[alias_product]
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
          except:
             import pdb; pdb.set_trace()          
             


sys.exit() # spostato prima questa parte:
#k2_ef={}
#k2_ef["DIMENSIONI BANCALE (AxBxC)"]=9
#k2_ef["pz/m³"]=10
#k2_ef["pz/epal"]=11
#k2_ef["DIMENSIONI IMBALLO (AxBxC)"]=8
#k2_ef["DIMENSIONI ARTICOLO (AxBxC)"]=7

convert_k2_2_oerp_id={}

convert_k2_2_oerp_id['9']=6   #bancale
convert_k2_2_oerp_id['10']=2  #m3
convert_k2_2_oerp_id['11']=3  #epal
convert_k2_2_oerp_id['8']=4   #imballo
convert_k2_2_oerp_id['7']=5   #articolo

convert_k2_2_oerp_id['12']=5
convert_k2_2_oerp_id['13']=4
convert_k2_2_oerp_id['14']=6
convert_k2_2_oerp_id['15']=2
convert_k2_2_oerp_id['16']=3

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
                                                                                





# Aggiorno gli alias portandoli a quelli di OpenERP:
#openerp.updateProductAlias#
#
#product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('web','=',True)])                 
#for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids, ['id', 'default_code', 'k2_alias']):

    
#product_item_id[product['default_code']]=product['id']
             



'''
          if sku==u'separ\xe8':
             c="550"
          else:
             c=alias[sku]
          if c:
             update_id=product_item_id[c]
             sock.execute(dbname, uid, pwd, 'product.product', 'write', update_id, {'web':True})
             try:             
                 os.rename("/home/administrator/photo/FiamLug2012/product/k2/%s.jpg"%(conver_image[c]), "/home/administrator/photo/FiamLug2012/product/k2/src/%s.jpg"%(c))
                 print "rename: k2/%s.jpg"%(conver_image[c]),"k2/srv/%s.jpg"%(c)
             except:
                 pass #print "[ERR] rename: /home/administrator/photo/FiamLug2012/product/k2/%s.jpg"%(conver_image[c]),"k2/srv/%s.jpg"%(c)

             for t in image_type:
                 try:             
                     os.rename("/home/administrator/photo/FiamLug2012/product/k2/%s_%s.jpg"%(conver_image[c],t), "/home/administrator/photo/FiamLug2012/product/k2/%s/%s.jpg"%(t,c))
                 except:
                     print "[ERR] rename: /home/administrator/photo/FiamLug2012/product/k2/%s_%s.jpg"%(conver_image[c],t), " to /home/administrator/photo/FiamLug2012/product/k2/%s/%s.jpg"%(t,c)
'''        
#if c:
#   print """echo "code['%s']='".md5('Image%s')."'<br />";"""%(c, item_id)
#print "%s. Title %s [%s]"%(i, title, sku)
#print "%s;%s"%(sku, title)
#print "alias['%s']=''"%(sku)

"""
INSERT INTO `joomla_fiam`.`jos_k2_items` (`id`, `title`, `alias`, `catid`, `published`, `introtext`, `fulltext`, `video`, `gallery`, `extra_fields`, `extra_fields_search`, `created`, `created_by`, `created_by_alias`, `checked_out`, `checked_out_time`, `modified`, `modified_by`, `publish_up`, `publish_down`, `trash`, `access`, `ordering`, `featured`, `featured_ordering`, `image_caption`, `image_credits`, `video_caption`, `video_credits`, `hits`, `params`, `metadesc`, `metadata`, `metakey`, `plugins`, `language`) VALUES (NULL, 'prova', 'prova', '1', '1', 'intro', 'full text', NULL, NULL, NULL, '', '', '0', '', '', '', '', '0', '', '', '0', '0', '0', '0', '0', '', '', '', '', '', '', '', '', '', '', '');


INSERT INTO `joomla_fiam`.`jos_k2_tags_xref` (`id`, `tagID`, `itemID`) VALUES (NULL, '3', '146');
3 from jos_k2_xref table
"""

