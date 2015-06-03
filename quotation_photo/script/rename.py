#-*- encoding: utf-8 -*-
#require installation of ghostscript on linux PC:
# sudo apt-get install ghostscript

import subprocess
import os
 
path_org = '/home/administrator/lp/openerp/server/bin/addons/quotation_photo_fiam/images/fiam/default/'
path_def = '/home/administrator/lp/openerp/server/bin/addons/quotation_photo_fiam/images/fiam/rename/'
progressivi={}

def if_intero(string):
    res=""
    for char in string:
       try: 
          char_int = int(char) 
          res += char
       except:
          pass #do nothing just jump
    return res
                    
def normalizza(file_name):
    # Pulisco gli extra _ finali << ottengo il codice pulito
    nome_max=13
    tipo="S" # per default metto S             

    if file_name[13:14] not in ("A", "S"): 
       if file_name[12:13] in ("A", "S"):  # caso <
          nome_max=12 # fermo un carattere prima
          tipo=file_name[12:13]
       elif file_name[14:15] in ("A", "S"): # caso >
          nome_max=13
          tipo=file_name[14:15]
       elif file_name[11:12] in ("A", "S"):  # caso <<
          nome_max=11 # fermo un carattere prima
          tipo=file_name[11:12]
       else:
          nome_max=13
          tipo="S" # per default metto S             
          
    nome=file_name[:nome_max]   
    nome=nome.replace("_"," ").strip()
    nome=nome.replace(" ","_")
    #tipo=file_name[13:14] # << ricavo il tipo immagine da qui
    if not tipo:
       tipo="S" # per default messo S
    #extra=if_intero(file_name[14:])  # << NON CONTEGGIATO (progressivo generato a caso)
    element="%s.%s"%(nome,tipo)
    if element in progressivi:
       progressivi[element]+=1
       extra="%02d"%(progressivi[element],)
    else:
       extra="%02d"%(1,)
       progressivi[element]=1
       
    return "%s.%s"%(element,extra) # TODO extra must converted i progressiv


for infile in os.listdir(path_org):
    if infile[-3:].lower()=="jpg": # lavoro sulle immagini già convertite
       orig_file=os.path.join(path_org, infile) 
       norm_file=normalizza(infile[:-4])

       if norm_file[-5:] in (".S.01",):
          dest_file=os.path.join(path_def, norm_file[:-5] + ".jpg") 
          command="cp '%s' '%s'"%(orig_file, dest_file) # doppione immagine
       else:          
          dest_file=os.path.join(path_def, norm_file + ".jpg") 
          command="cp '%s' '%s'"%(orig_file,dest_file)
       esito=subprocess.call([command,],shell=True)

    print "%s >> %s"%(infile, norm_file)
    # Ciclo per creare il file senza niente
       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
