#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ETL. import csv file with preformatted data comes from Mexal orders
# use: import.csv mexal_file_csv.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser, datetime
from posta import *
import sys, time, os # for get date of file

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import_fatturato.py fatmeseoerp.FIA
         *********************
         """
   sys.exit()

# Funzioni:
def prepare(valore):
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def prepare_date(valore):
    valore=valore.strip()
    if len(valore)==8:
       if valore: # TODO test correct date format
          return valore[:4] + "/" + valore[4:6] + "/" + valore[6:8]
    return '' #time.strftime("%d/%m/%Y") (per gli altri casi)

def prepare_float(valore):
    valore=valore.strip()
    if valore: # TODO test correct date format
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

def get_partner_id(sock, uid, pwd, mexal_id):
    ''' Ricavo l'ID del partner dall'id di mexal
    '''
    item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', mexal_id)])
    if item_id:
       return item_id[0]
    return 0

def get_partner_name(sock, uid, pwd, partner_id):
    ''' Ricavo il nome del partner
    '''
    partner_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id)
    if partner_read:
       return partner_read['name']
    return ''

FileInput = sys.argv[1]
if FileInput:
   sigla_azienda = FileInput[-3:].lower()
else:
   print "[ERR] File input non presente!"
   sys.exit()
if sigla_azienda in ('gpb','fia'):
   cfg_file = sigla_azienda + ".openerp.cfg"
else:
   print "[ERR] Sigla azienda non trovata!"
   sys.exit()

# Ricavo la data del file per comunicarla
create_date=time.ctime(os.path.getctime(FileInput))

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname = config.get('dbaccess','dbname')
user = config.get('dbaccess','user')
pwd = config.get('dbaccess','pwd')
server = config.get('dbaccess','server')
port = config.get('dbaccess','port')
separator = config.get('dbaccess','separator')
verbose = eval(config.get('import_mode','verbose'))

verbose = False # TODO togliere
debug = True

smtp_sender = config.get('smtp', 'sender')
smtp_receiver = config.get('smtp', 'receiver')
smtp_subject = config.get('smtp', 'subject') + " (Importazione fatturato cliente)"
smtp_text = config.get('smtp', 'text')
smtp_log = config.get('smtp', 'log_file') + ".fatturato.csv"
smtp_server = config.get('smtp', 'server')

# Open file log error (if verbose mail the file are sent to admin email)
try:
   out_file = open(smtp_log,"w")
except:
   print "[WARNING]","Error creating log files:", smtp_log
   # No raise as it'a a warning

header_lines = 0 # mai da mexal

# XMLRPC connection for autentication (UID) and proxy
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Elimino tutto
errore_da_comunicare = False
print "Elimino vecchio archivio invoice!"

elimino_invoice = sock.execute(dbname, uid, pwd, 'statistic.invoice', 'unlink',
    sock.execute(dbname, uid, pwd, 'statistic.invoice', 'search', []))
elimino_trend = sock.execute(dbname, uid, pwd, 'statistic.trend', 'unlink',
    sock.execute(dbname, uid, pwd, 'statistic.trend', 'search', []))
elimino_trendoc = sock.execute(dbname, uid, pwd, 'statistic.trendoc', 'unlink',
    sock.execute(dbname, uid, pwd, 'statistic.trendoc', 'search', []))

print "Inizio importazione"
# TODO portare parametrizzandolo in OpenERP:
customer_replace = {# Cust. Company 2: (Cust. Company 1, Reseller Company 1)
    '06.40533': (# Customer code Company2
        (            # Customer code Company 1
        '06.02209',
        get_partner_id(sock, uid, pwd, '06.02209'),
        get_partner_name(sock, uid, pwd, get_partner_id(sock, uid, pwd, '06.02209')),
        ),           # Customer name Company 1
        ('06.01537',
        get_partner_id(sock, uid, pwd, '06.01537'),
        get_partner_name(sock, uid, pwd, get_partner_id(sock, uid, pwd, '06.01537')),
        ),
        ) }

loop_steps = {
    1: csv.reader(open(FileInput, 'rb'), delimiter=separator),
    2: csv.reader(open("%sGPB" % FileInput[:-3], 'rb'), delimiter=separator),
}

try:
    for step, lines in loop_steps.iteritems():
        counter = {'tot': -header_lines, 'new':0, 'upd':0} # tot negative (jump N lines)
        tot_col = 0
        # Carico gli elementi da file CSV:
        for line in lines:
            if tot_col == 0: # memorizzo il numero colonne la prima volta
                tot_col = len(line)
                print "[INFO] Colonne rilevate", tot_col
                raise_error("[INFO] Procedura: %s \n\tFile importato: %s [creazione: %s]" % (
                    sys.argv, FileInput, create_date), out_file) # comune per tutte e due (non personalizzo il nome file)
            if counter['tot'] < 0:  # salto le N righe di intestazione
                counter['tot'] += 1
            else:
                if len(line) and (tot_col == len(line)): # salto le righe vuote e le righe con colonne diverse
                    counter['tot'] += 1
                    try:
                        mexal_id = prepare(line[0])                   # Codice cliente di mexal forma (NNN.NNNNN)
                        month = int(prepare(line[1]) or 0)            # Mese
                        year = prepare(line[2])                       # Anno
                        total_invoice = prepare_float(line[3]) or 0.0 # Totale
                        type_document = prepare(line[4]).lower()      # Type (oc or ft)

                        if step == 2: # Particolarità seconda passata
                            if mexal_id not in customer_replace:
                                continue # jump line if not a replace partner

                            # Cliente sostituito a cui va attribuito il ricavo:
                            old_mexal_id = mexal_id
                            mexal_id = customer_replace[old_mexal_id][0][0]
                            partner_id = customer_replace[old_mexal_id][0][1]
                            partner_name = customer_replace[old_mexal_id][0][2]

                            # Agente a cui va il valore in negativo:
                            mexal_id2 = customer_replace[old_mexal_id][1][0]
                            partner_id2 = customer_replace[old_mexal_id][1][1]
                            partner_name2 = customer_replace[old_mexal_id][1][2]

                        else: # Particolarità prima passata
                            # Problema M Business:
                            if mexal_id in (
                                '06.00052', '06.00632', '06.01123', '06.01125', 
                                '06.01126', '06.01127', '06.01129', '06.01131',
                                '06.01132', '06.01136', '06.01137', '06.01138', 
                                '06.01139', '06.01142', '06.01143', '06.01146',
                                '06.01147', '06.01149', '06.01151', '06.01153',
                                '06.01154', '06.01155', '06.01159', '06.01161',
                                '06.01163', '06.01164', '06.01165', '06.01166',
                                '06.01167', '06.01168', '06.01170', '06.01171',
                                '06.01175', '06.01177', '06.01178', '06.01179',
                                '06.01221', '06.01231', '06.01260', '06.01317',
                                '06.01386', '06.01408', '06.01416', '06.01420',
                                '06.01421', '06.01424', '06.01436', '06.01439',
                                '06.01481', '06.01501', '06.01532', '06.01538', 
                                '06.01580', '06.01609', '06.01764', '06.01797',
                                '06.02081', '06.02117', '06.02348', '06.02408',
                                '06.02409', '06.02709', '06.02888', '06.03043',
                                '06.03629', '06.03788', ):
                                
                                raise_error("[WARNING] Riga %s: sostituito codice: %s con: 06.03044 (Problema M Business)" % (
                                    counter['tot'], mexal_id), out_file)
                                mexal_id = '06.03044'

                            # Calculated field:
                            partner_id = get_partner_id(sock, uid, pwd, mexal_id)
                            if not partner_id:
                                raise_error("[ERR] Riga: %s Partner non trovato, codice: %s" % (
                                    counter['tot'], mexal_id), out_file)
                                errore_da_comunicare = True
                                partner_name = ">> Partner non trovato %s" % (
                                    mexal_id or "")
                            else:
                                partner_name = get_partner_name(
                                    sock, uid, pwd, partner_id)

                        if not total_invoice:
                            if verbose:
                                raise_error("[WARN] Riga: %s Importo non trovato! Riga: %s" % (
                                    counter['tot'], line, ), out_file)                                
                                continue # Nessun errore può capitare

                        if not (month or year): # lo importo lo stesso così si vede nei non class.
                            raise_error("[ERR] Riga: %s Mese o anno non trovato (importato lo stesso)! %s" % (
                                counter['tot'], line, ), out_file)
                            errore_da_comunicare = True

                        # Attualizzo gli OC se sono più vecchi di oggi
                        if (type_document == 'oc') and ("%s%02d" % (year, month) < datetime.datetime.now().strftime("%Y%m")):
                            if debug:
                                raise_error("[DEBUG] Attualizzo OC datato: %s%02d, riga %s, cliente: %s, totale %s" % (
                                    year, month, counter['tot'], mexal_id, total_invoice), out_file)
                            year = datetime.datetime.now().strftime("%Y")
                            month = int(datetime.datetime.now().strftime("%m"))

                        data = {
                            "name": "%s [%s]" % (partner_name, mexal_id),
                            "partner_id": partner_id,
                            "month": month,
                            "type_document": type_document,
                        }

                        # Calcolo in quale anno inserire il fatturato (specchio di 3)
                        anno_mese = "%s%02d" % (year, month)

                        anno_attuale = int(datetime.datetime.now().strftime("%Y"))
                        mese_attuale = int(datetime.datetime.now().strftime("%m"))

                        if mese_attuale >= 1 and mese_attuale <= 8:
                            anno_riferimento = anno_attuale - 1 # la stagione è partita l'anno scorso
                        elif mese_attuale >= 9 and mese_attuale <= 12:
                            anno_riferimento = anno_attuale  # la stagione è partita l'anno scorso
                        else:
                            raise_error("[ERR] Riga: %s - Errore mese attuale (non >=1 e <=12)" % (
                                counter['tot']), out_file)
                            errore_da_comunicare = True

                        # Periodo settembre - anno attuale >> agosto - anno prossimo
                        if anno_mese >= "%s09" % (anno_riferimento,) and anno_mese <= "%s08" % (anno_riferimento + 1, ):      # current
                            data['total'] = total_invoice
                        elif anno_mese >= "%s09" % (anno_riferimento -1, ) and anno_mese <= "%s08" % (anno_riferimento, ):    # anno -1
                            data['total_last'] = total_invoice
                        elif anno_mese >= "%s09" % (anno_riferimento -2, ) and anno_mese <= "%s08" % (anno_riferimento -1, ): # anno -2
                            data['total_last_last'] = total_invoice
                        elif anno_mese >= "%s09" % (anno_riferimento -3, ) and anno_mese <= "%s08" % (anno_riferimento -2, ): # anno -3
                            data['total_last_last_last'] = total_invoice
                        elif anno_mese >= "%s09" % (anno_riferimento -4, ) and anno_mese <= "%s08" % (anno_riferimento -3, ): # anno -4
                            data['total_last_last_last_last'] = total_invoice
                        else:
                            continue # salto riga # saltato comunicazione per i valori extra periodo di valutazione (conseguenza delle nuove modifiche

                        try:
                            # Creo la voce positiva corretta (parte comune)
                            invoice_id = sock.execute(dbname, uid, pwd,
                                'statistic.invoice', 'create', data)
                            if step == 2: # Creo il secondo pagamento in negativo
                                # Inverto i segni e imposto l'agente (solo 2):
                                data['name'] = "%s [%s]" % (partner_name2, mexal_id2)
                                data['partner_id'] = partner_id2
                                data['total'] = -data.get(
                                    'total', 0.0)
                                data['total_last'] = -data.get(
                                    'total_last', 0.0)
                                data['total_last_last'] = -data.get(
                                    'total_last_last', 0.0)
                                data['total_last_last_last'] = -data.get(
                                    'total_last_last_last', 0.0)
                                data['total_last_last_last_last'] = -data.get(
                                    'total_last_last_last_last', 0.0)
                                invoice_id = sock.execute(dbname, uid, pwd,
                                    'statistic.invoice', 'create', data)
                        except:
                            raise_error("[ERR] Riga: %s Errore creando fatturato: %s" % (
                                counter['tot'], mexal_id), out_file)
                            errore_da_comunicare = True
                        if verbose:
                            raise_error("[INFO] Riga: %s Fatturato inserito: %s" % (
                                counter['tot'], mexal_id), out_file)
                    except:
                        raise_error("[ERR] Riga: %s Errore di importazione: %s" % (
                            counter['tot'], sys.exc_info()[0]), out_file)
                        errore_da_comunicare = True
                else:
                    raise_error("[ERR] Riga: %s Riga vuota o con colonne diverse: col attuale=%s col effettive=%s" % (
                        counter['tot'], tot_col, len(line)), out_file)
                    errore_da_comunicare = True
        raise_error("[INFO] Importazione terminata! Totale elementi %s" % (
            counter['tot'], ), out_file)

    # Parte comune fuori dal ciclo multi step:
    for documento in ['oc', 'ft', 'bc',]:
        print "Ricavo i dati per statistic.trend" + documento # Fatture e OC + Fatture
        if documento == "ft": # Solo fatture
           invoice_ids = sock.execute(
               dbname, uid, pwd, 'statistic.invoice', 'search', [
                   ('type_document','=','ft')])
        else: # tutto oc + ft + bc
           invoice_ids = sock.execute(
               dbname, uid, pwd, 'statistic.invoice', 'search', [])

        if invoice_ids: # Elimino precedenti
            if documento == "ft":
               trend_ids = sock.execute(dbname, uid, pwd, 'statistic.trend',
                   'search', [])
               remove_trend = sock.execute(dbname, uid, pwd, 'statistic.trend',
                   'unlink', trend_ids)
            else:
               trend_ids = sock.execute(dbname, uid, pwd, 'statistic.trendoc',
                   'search', [])
               remove_trend = sock.execute(dbname, uid, pwd, 'statistic.trendoc',
                   'unlink', trend_ids)

            # Carico nella lista tutti i valori divisi per partner:
            item_list = {}
            # Causa aggiunte posteriori il pos 3 = anno -3, pos 4 = anno -4
            total_invoiced = [0.0, 0.0, 0.0, 0.0, 0.0] # -2, -1, 0 -4, -3,
            for item in sock.execute(dbname, uid, pwd, 'statistic.invoice', 'read', invoice_ids): # in funzione del documento
                partner_id = (item['partner_id'] and item['partner_id'][0]) or 0

                if partner_id not in item_list:
                    # stesso discorso per l'aggiunta a posteriori
                    item_list[partner_id] = [0.0, 0.0, 0.0, 0.0, 0.0] # -2 -1 0 -4, -3,

                if item['total']:                                  # anno attuale
                    item_list[partner_id][2] += item['total']
                    total_invoiced[2] += item['total']
                if item['total_last']:                             # anno -1
                    item_list[partner_id][1] += item['total_last']
                    total_invoiced[1] += item['total_last']
                if item['total_last_last']:                        # anno -2
                    item_list[partner_id][0] += item['total_last_last']
                    total_invoiced[0] += item['total_last_last']
                if item['total_last_last_last']:                   # anno -3
                    item_list[partner_id][3] += item['total_last_last_last']
                    total_invoiced[3] += item['total_last_last_last']
                if item['total_last_last_last_last']:              # anno -4
                    item_list[partner_id][4] += item['total_last_last_last_last']
                    total_invoiced[4] += item['total_last_last_last_last']

        print "Inserisco i dati nell'archivio statistico per " + documento
        for elemento_id in item_list.keys(): # passo tutti gli elementi inserendoli in archivio col calcolo perc.
            data = {
                'name': "cliente: %d" % (elemento_id,), #"%s [%d €]" % (number, total) ,
                'partner_id': elemento_id,
                'total': item_list[elemento_id][2],
                'total_last': item_list[elemento_id][1],
                'total_last_last': item_list[elemento_id][0],
                'total_last_last_last': item_list[elemento_id][3],
                'total_last_last_last_last': item_list[elemento_id][4],
                'percentage': (total_invoiced[2]) and (item_list[elemento_id][2] * 100 / (total_invoiced[2])), # current year
                'percentage_last': (total_invoiced[1]) and (item_list[elemento_id][1] * 100 / (total_invoiced[1])), # -1 year
                'percentage_last_last': (total_invoiced[0]) and (item_list[elemento_id][0] * 100 / (total_invoiced[0])), # -2 year
                # percentage_last_last_last
                # percentage_last_last_last_last
                }
            try:
               if documento=="ft":
                  trend_id = sock.execute(dbname, uid, pwd, 'statistic.trend', 'create', data)
               else:
                  trend_id = sock.execute(dbname, uid, pwd, 'statistic.trendoc', 'create', data)

            except:
               raise_error("[ERR] Errore creando ordine id_partner: %s" % (
                   elemento_id,), out_file)
               errore_da_comunicare=True
            if verbose:
               raise_error("[INFO] Fatturato del partner %d inserito:" % (
                   elemento_id,), out_file)

        if debug:
           print item_list
    out_file.close()
except:
    print raise_error('[ERR] Errore importando gli ordini!', out_file)

send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)

