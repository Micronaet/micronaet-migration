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


tree = ET.parse('jos_modules_gallery.xml')
root = tree.getroot()
table = "jos_modules"

for child in root: # tabelle nel DB
    if child.attrib['name']==table: # is a record of table selected
       item_id = 0
       title = content = published = ""

       for column in child:       
           if column.attrib['name']=="id":
               item_id=column.text 
           if column.attrib['name']=="title":
               title=column.text 
           if column.attrib['name']=="params":
               params=column.text 
           if column.attrib['name']=="published":
               published=column.text 
               
       if published == "1":           
          folder_name= params.split("\n")[0].split("/")[-2:-1][0] # name of folder
          category_ids = sock.execute(dbname, uid, pwd, 'web.k2.gallery', 'search', [('name','=',folder_name)])
          if category_ids: 
             update= sock.execute(dbname, uid, pwd, 'web.k2.gallery', 'write', category_ids[0], {'k2_id': int(item_id),
                                                                                                 'long_title': title,
                                                                                                })
             print "UPDATE: ", title                                                                      
          else:
             record_id = sock.execute(dbname, uid, pwd, 'web.k2.gallery', 'create', {'name': folder_name,
                                                                                     'k2_id': int(item_id),
                                                                                     'long_title': title,
                                                                                     })
             print "CREATE: ", title                                                                      
                                                                                        

