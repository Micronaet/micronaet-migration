#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import csv, pdb
from datetime import datetime

def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    #valore=valore.decode('cp1252')
    #valore=valore.encode('utf-8')
    return valore.strip()

def PrepareFloat(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

def Intero(valore):
    try:
        return valore.replace(",",".").split(".")[0]
    else:
       return "0"

# Initialize variables
# Controllo elementi da ignorare:
spots=[r"310/24", r"37100", r"47584", r"47588", 
      r"47596", r"504", r"656/1", r"661/60", 
      r"671/60", r"671/60", r"8122/6", r"8123/0", 
      r"8192/6", r"8213/0", r"822MEDITERRANEO",
      r"8333/0", r"8452/6", r"8842/6", ]

ranges=[]
"""[r"00100", r"0741/6"], [r"0813/26", r"09802"], 
       [r"0813/26", r"09802"], [r"119TX ANMG", r"169"],
       [r"210", r"212/45"], [r"215", r"216BL VE"],
       [r"220 TELAIO", r"241/20"], [r"265/205", r"30140"],
       [r"311/2", r"311/27"], [r"320", r"321/22"], 
       [r"322/1", r"322/43"], [r"326/1", r"331/60"], 
       [r"340 TELAIO", r"341/22"], [r"342/1", r"342/45"],
       [r"360/33", r"361/60"],  [r"383", r"412/42"],
       [r"420  BIBE", r"422/45"], [r"430/25", r"431/60"], 
       [r"440  CI", r"440/42"], [r"44461", r"44462"], 
       [r"450", r"450/42"], [r"451/1", r"451/22"],
       [r"452/1", r"460/42"], [r"461/1", r"461/2"], 
       [r"462/1", r"462/45"], [r"470 BIBE", r"470/5"],
       [r"471", r"471/1"], [r"483 TELAIO", r"483/1S"],
       [r"500  CI", r"501VAM"], [r"510 TELAIO", r"522/46"],
       [r"530/2", r"570/25"], [r"60", r"610/42"],
       [r"611/1", r"612/45"], [r"620", r"620/8"],
       [r"621/1", r"621/2"], [r"632/42", r"651/3 VETUS"],                   
       [r"691/1", r"692/43"], [r"711/0", r"711/5"], 
       [r"722/0", r"731/2"], [r"743", r"744/2"], 
       [r"8013/0", r"80332"], [r"8112/6", r"8113/1"],
       [r"8453/0", r"8463/29"], [r"8521/25", r"8543/0"],
       [r"861", r"8693/2"], [r"8711/6", r"8743/6"], 
       [r"8973/0", r"900"], [r"910VE", r"99VERDE"],
       [r"C049TX", r"C071"], [r"CALOR", r"CUSCNEU28CSS"], ]    """

FileInputGPB = 'esistoerp.TMP'  # comes from mexal
FileInputFIA = 'esistoerp.FIA'
FileInputPrenotati = 'ocredoerp.GPB' # OC Re Desiderio (Prenotazioni)
FileOutput = 'esistoerp.GPB'    # File to publish
FileOCdate = 'ofoerp'    # Merce in arrivo
FileEsito='esito.txt'

fout = open(FileOutput, 'w')
fesito = open(FileEsito, 'w')

# Carico in un dict tutte le date di consegna:
dettaglio_arrivi_oc={}
numero_arrivi_oc={}
try:
    for azienda in ["GPB", "FIA"]:
        lines = csv.reader(open(FileOCdate + "." + azienda, 'rb'), delimiter=";")
        for line in lines:
            if len(line): 
               codice = Prepare(line[0]).upper()
               quant=PrepareFloat(line[1])
               data=Prepare(line[2])
               if data:
                  data = "%s - %s/%s/%s"%(quant, data[-2:],data[4:6],data[2:4])
               else:   
                  data = "%s - ??/??/??"%(quant,)
                  
               if azienda=="FIA": 
                   if codice[0:2] in ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", ]: # I codici abbinati cominciano per C in fiam
                      if codice[1:] in numero_arrivi_oc:
                         numero_arrivi_oc[codice[1:]] += 1
                      else:   
                         numero_arrivi_oc[codice[1:]] = 1 # se non esiste è inizializzato a 1
                   
                      if codice[1:] in dettaglio_arrivi_oc:
                         dettaglio_arrivi_oc[codice[1:]] = dettaglio_arrivi_oc[codice[1:]] + "<br>" + data + " (F)"
                      else:   
                         dettaglio_arrivi_oc[codice[1:]] = data+ " (F)"
               else: # GPB   
                   if codice in numero_arrivi_oc:
                      numero_arrivi_oc[codice] += 1
                   else:   
                      numero_arrivi_oc[codice] = 1 # se non esiste è inizializzato a 1

                   if codice in dettaglio_arrivi_oc:
                      dettaglio_arrivi_oc[codice] = dettaglio_arrivi_oc[codice] + "<br>" + data 
                   else:   
                      dettaglio_arrivi_oc[codice] =  data
except:
    print '>>> [ERROR] Error importando gli ordini!'
    raise 

# Carico tutto il file fiam in un dict
lines = csv.reader(open(FileInputFIA,'rb'), delimiter=";")
dispo_fiam={}
try:
    for line in lines: 
        if len(line): 
           codice= Prepare(line[0]).upper()
           descrizione=Prepare(line[1]) #"%s (EUR %s)"%(Prepare(line[1]),Prepare(line[4]) or "0")  #Prendo il listino 4 per Fiam
           dispo=(PrepareFloat(line[2]))
           arrivi=(PrepareFloat(line[3]))
           prezzo=Prepare(line[4]) or "0"
           if codice[0:2] in ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", ]: # I codici abbinati cominciano per C in fiam
              dispo_fiam[codice[1:]]=[dispo, arrivi, descrizione, prezzo]
except:
    print '>>> [ERROR] Error importing Fiam file!'
    raise 

# Carico tutto il file delle prenotazioni in un dict
lines = csv.reader(open(FileInputPrenotati,'rb'), delimiter=";")
prenotazioni_desiderio={}
try:
    for line in lines: 
        if len(line): 
           codice= Prepare(line[0]).upper()
           quantita=PrepareFloat(line[1])
           prenotazioni_desiderio[codice]=quantita
except:
    print '>>> [ERROR] Error importing Re Desiderio file!'
    raise 

# Leggo e aggiusto il file GPB per riespostarlo completo
lines = csv.reader(open(FileInputGPB,'rb'), delimiter=";")
dispo_gpb=[]
try:
    '''Controllo tutte le righe del file GPB
       Verifico che non ci siano dei codici da scartare:
                1. iniziale del codice
                2. codice particolare
                3. range di codici
       Se non viene scartato:
       Verifico che non ci sia il codice in Fiam (eventualmente sommo la disponibilità e gli arrivi)
       Salvo tutti i codici scritti (servirà poi per scartare e scrivere quelli presenti
       solamente in Fiam
       Se il codice è presente nell'elenco degli ordini in arrivo viene aggiunto anche
       il pezzo di questo dato (totale, data)
           
    '''
    tot=0
    for line in lines:
        if len(line): 
           codice = Prepare(line[0]).upper()
           descrizione = Prepare(line[1]) #"%s (EUR %s)"%(Prepare(line[1]),Prepare(line[5]) or "0")  #Prendo il listino 1 per GPB
           dispo = PrepareFloat(line[2])
           arrivi = PrepareFloat(line[3])
           prezzo = Prepare(line[5]) or "0"
           
           # Verifica se prendere in considerazione il codice: #################
           if codice in prenotazioni_desiderio:     
              prenotati=prenotazioni_desiderio[codice] # prenotazione Re Desiderio
           else:
              prenotati=0.0 
           if codice[0] in ["A", "B", "D", "E", "F", "G", "I", "K", "L", "M", "N", "O", "P", "R", "S", "T", "V", "W", "Z"]:
              print "SCART:", codice, descrizione # nessun articolo che comincia con queste lettere
           elif codice in spots:
              print "SCART:", codice, descrizione
           else:
              scartato=False
              for range_no in ranges:
                  if codice >= range_no[0] and codice <= range_no[1]:
                     print "SCART:", codice, descrizione
                     scartato=True
                     break # exit for
              # Fine verifica da qui preparo la scrittura dell'elemento: #######       
              if not scartato: # Sommo eventuale magazzino Fiam e scrivo il file
                 print "PRESO:", codice, descrizione
                 if codice in dispo_fiam: # il codice GPB c'è nelle disponibilità della Fiam
                    dispo += dispo_fiam[codice][0]
                    arrivi += dispo_fiam[codice][1]
                 dispo_gpb.append(codice) # Salvo il codice per migrare le dispo fiam poi   
                 arrivi = str(arrivi).replace(".",",")                       
                 if codice in dettaglio_arrivi_oc: # Se questo codice ha anche futuri arrivi (OF: q. - data)
                    if numero_arrivi_oc[codice]==1: # Se questo codice ha anche futuri arrivi (OF: q. - data)
                       if dettaglio_arrivi_oc[codice]: # Se esiste l'OF
                          arrivi = dettaglio_arrivi_oc[codice]
                       else:
                          arrivi = "<b>" + arrivi + "</b><br>" # caso strano c'è ordinato ma manca OF                     
                    else:                
                       arrivi = "<b>" + arrivi + "</b><br>" + dettaglio_arrivi_oc[codice]
                                        
                 if not arrivi: # capita che diventa vuoto!
                    arrivi="0,0"
                 dispo = str(dispo).replace(".",",") 
                 prenotati=str(prenotati).replace(".",",")
                 tot+=1
                 s = codice + ";" + descrizione.replace("Ø", "diam.").replace("ø", "diam.") + ";" + Intero(dispo) + ";" + Intero(arrivi) + ";" + Intero(prenotati) + ";"  + prezzo + "\n"
                 fout.write(s)
                 
    ''' Inserisco gli articoli + desc + dispo + arrivo + (re desiderio)
        Routine per i codici presenti in Fiam e non presenti in GPB
        Viene anche calcolato il totale oc in arrivo 
        Non viene calcolato l'ordinato per Re Desiderio perchè è presente solo in GPB
    '''
    for codice in dispo_fiam.keys():
        if codice not in dispo_gpb: # Se il codice non è presente nei codici per GPB:
           descrizione=dispo_fiam[codice][2].replace("Ø", "diam.").replace("ø", "diam.")
           arrivi=dispo_fiam[codice][1] 
           if codice in dettaglio_arrivi_oc: # Verifico se vanno sommati gli OF
              if numero_arrivi_oc[codice]==1: # Se questo codice ha anche futuri arrivi (OF: q. - data)
                 if dettaglio_arrivi_oc[codice]:
                    arrivi = dettaglio_arrivi_oc[codice]
                 else:
                    arrivi = "<b>" + arrivi + "</b><br>"  # caso strano c'è ordinato ma manca OF
              else:                
                 arrivi = "<b>" + arrivi + "</b><br>" + dettaglio_arrivi_oc[codice]
           if not arrivi: # capita che diventa vuoto!
              arrivi="0,0"

           dispo=str(dispo_fiam[codice][0]).replace(".",",") # non devo sommare dispo GPB!
           arrivi=str(arrivi).replace(".",",")   
           tot+=1 
           s = codice + " (F);" + descrizione + ";" + Intero(dispo) + ";" + Intero(arrivi) + ";0;" + Intero(dispo_fiam[codice][3]) + "\n" #(F) = codice presente solo in Fiam
           fout.write(s)
    fout.close()

    aggiornamento=datetime.now()                  
    fesito.write(aggiornamento.strftime("%d-%m-%Y %H:%M"))
    fesito.write(";")
    fesito.write(str(tot))
    fesito.close()
except:
    print '>>> [ERROR] Error!'
    raise 
