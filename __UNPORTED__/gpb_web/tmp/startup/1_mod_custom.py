#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xml.etree.ElementTree as ET
import xmlrpclib, sys, os

dbname="FiamLug2012"
user="admin"
pwd="cgp.fmsp6"
server="localhost"
port="8069"

#context={'lang':'it_IT','tz':False} #Set up an italian context 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)


tree = ET.parse('jos_modules.xml')
root = tree.getroot()
table = "jos_modules"

import pdb; pdb.set_trace()
for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       item_id = 0
       showtitle = title = content = published = ""

       for column in child:       
           if column.attrib['name']=="id":
               item_id=column.text 
           if column.attrib['name']=="title":
               title=column.text 
           if column.attrib['name']=="content":
               content=column.text 
           if column.attrib['name']=="published":
               published=column.text 
           if column.attrib['name']=="showtitle":
               showtitle=column.text 

       if published == "1":           
          category_ids = sock.execute(dbname, uid, pwd, 'web.k2.mod.custom', 'search', [('name','=',title)])
          if category_ids: 
             update= sock.execute(dbname, uid, pwd, 'web.k2.mod.custom', 'write', category_ids[0], {'k2_id': int(item_id),
                                                                                                    'text': content,
                                                                                                    'has_title': True if showtitle=="1" else False,
                                                                                                   })
             print "UPDATE: ", title                                                                      
          else:
             record_id = sock.execute(dbname, uid, pwd, 'web.k2.mod.custom', 'create', {'name': title,
                                                                                        'k2_id': int(item_id),
                                                                                        'text': content,
                                                                                        'has_title': True if showtitle=="1" else False,
                                                                                        })
             print "CREATE: ", title                                                                      
                                                                                        

