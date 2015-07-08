# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import xmlrpclib
import csv
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class StatisticHeader(orm.Model):
    _name = 'statistic.header'

class StatisticOrder(orm.Model):
    '''Object that contain all order header coming from accounting
       This is only for statistic view or graph
    '''
    _name = 'statistic.order'
    _description = 'Statistic order'

    _order='sequence'

    _columns = {
        'name': fields.char('Description', size=64),
        'visible': fields.boolean('Visible',),
        'sequence': fields.integer('Sequence'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'property_account_position': fields.related('partner_id',
            'property_account_position', type='many2one',
            relation='account.fiscal.position', store=True,
            string='Fiscal position'),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)),
        'country_id': fields.related(
            'partner_id', 'country', type='many2one',
            relation='res.country', string='Country', store=True),
        'zone_id': fields.related(
            'partner_id', 'zone_id', type='many2one',
            relation='res.partner.zone', string='Zona', store=True),
        # Parte delle righe dettaglio:
        'code': fields.char('Code', size=24),
        'article': fields.char('Article', size=64),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'colli': fields.integer('Colli'),
        'quantity_ok': fields.float('Prodotti', digits=(16, 2)),
        'type': fields.selection([
            ('b','Prodotto'),
            ('n','Annullato'),
            ], 'Type of line'),
        'line_type': fields.selection([
            ('a','Articolo'),
            ('d','Descrizione'),
            ], 'Line type'),

        # Parte calcolata da visualizzare per prodotto:
        'total_linear_meter': fields.float('Total m/l', digits=(16, 2)),
        'total_volume': fields.float('Total volume', digits=(16, 2)),
        'total_weight': fields.float('Total weight', digits=(16, 2)),
        'note': fields.char('Note', size=64),

        'header_id': fields.many2one('statistic.header', 'Dettagli'),
        }

class StatisticHeader(orm.Model):
    _inherit = 'statistic.header'

    _order = 'deadline, name'
    _description = 'Testate ordini'

    # -------------------------------------------------------------------------
    #                           Scheduled procedure:
    # -------------------------------------------------------------------------
    def scheduled_import_order(self, cr, uid, file_input='~/etl/ocdetoerp.csv', 
            delimiter=';', header=0, verbose=100, context=None):
        ''' Import order for delivery report
        '''    

        def prepare_date(valore):
            valore=valore.strip()
            if len(valore)==8:
               if valore: # TODO test correct date format
                  return valore[:4] + "/" + valore[4:6] + "/" + valore[6:8]
            return '' #time.strftime("%d/%m/%Y") (per gli altri casi)

        def get_partner_id(sock, uid, pwd, mexal_id):
            ''' Ricavo l'ID del partner dall'id di mexal
            '''
            item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', mexal_id)])
            if item_id:
               return item_id[0]
            return 0   

            
        # Ricavo la data del file per comunicarla
        #create_date = time.ctime(os.path.getctime(FileInput))    

        lines = csv.reader(open(FileInput,'rb'), delimiter=delimiter)
        counter = 0

        # Remove all previous record:
        header_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, header_ids, context=context) 

        order_pool = self.pool.get('statistic.order')
        order_ids = order_pool.search(cr, uid, [], context=context) 
        order_pool.unlink(cr, uid, order_ids, context=context)
        
        # Carico gli elementi da file CSV:
        tot_col = 0
        header_id = 0
        old_order_number = ''
        sequence = 0
        try:
            for line in lines:
                if tot_col==0: # memorizzo il numero colonne la prima volta
                   tot_col=len(line)
                   print "[INFO] Colonne rilevate", tot_col
                   raise_error("[INFO] Procedura: %s \n\tFile importato: %s [creazione: %s]"%(sys.argv, FileInput, create_date), out_file)
                if counter['tot']<0:  # salto le N righe di intestazione
                   counter['tot']+=1
                else:   
                   if len(line) and (tot_col==len(line)): # salto le righe vuote e le righe con colonne diverse
                       counter['tot']+=1 
                       try:
                           csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                           mexal_id = prepare(line[csv_id])
                           csv_id+=1      # Cliente descrizione
                           cliente = prepare(line[csv_id]) 
                           csv_id+=1      # Order number
                           number = prepare(line[csv_id])
                           csv_id+=1      # Data OC formato: YYYYMMDD
                           order_date = prepare_date(line[csv_id]) or False
                           csv_id+=1      # Scadenza OC formato: YYYYMMDD
                           order_deadline = prepare_date(line[csv_id]) or False
                           csv_id+=1      # Articolo
                           articolo_id = prepare(line[csv_id]) 
                           csv_id+=1      # Articolo descrizione   (oppure campo campo note nelle righe (D)escrittive )
                           articolo = prepare(line[csv_id]) 
                           csv_id+=1      # Quantity
                           quantity = prepare_float(line[csv_id]) or 0.0
                           csv_id+=1      # Tipo di riga (b si intende prodotto)
                           type_of_line = prepare(line[csv_id]) 
                           csv_id+=1      # Note
                           note = prepare(line[csv_id]) 

                           csv_id+=1      # Descrizione italiano
                           product_description = prepare(line[csv_id]) 
                           csv_id+=1      # Descrizione inglese
                           product_description_eng = prepare(line[csv_id]) 
                           csv_id+=1      # Numero colli
                           colli = prepare(line[csv_id]) 
                           csv_id+=1      # Tipo di riga (A o D)
                           line_type = prepare(line[csv_id]).lower() # a=articolo, d=descrizione

                           csv_id+=1      # Codice porto
                           port_code = prepare(line[csv_id]).lower()
                           csv_id+=1      # Descrizione italiano
                           port_description = prepare(line[csv_id]) 
                           csv_id+=1      # Destinazione descrizione
                           destination_description = prepare(line[csv_id]) 
                           csv_id+=1      # Destinazione indirizzo
                           destination_address = prepare(line[csv_id]) 
                           csv_id+=1      # Destinazione CAP
                           destination_cap = prepare(line[csv_id]) 
                           csv_id+=1      # Destinazione localita'
                           destination_loc = prepare(line[csv_id]) 
                           csv_id+=1      # Destinazione provincia
                           destination_prov = prepare(line[csv_id]) 

                           # Videata extra:
                           csv_id+=1      # Data di registrazione
                           registration_date = prepare_date(line[csv_id]) or False
                           csv_id+=1      # Note aggiuntive (nella stampa)
                           extra_note = prepare(line[csv_id]) 
                           csv_id+=1      # Note aggiuntive (nella stampa)
                           agent_description = prepare(line[csv_id]) 

                           # Calculated field:
                           # Dati dimensionali letti dal prodotto:
                           product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id','=', articolo_id )])  

                           if product_ids and line_type == 'a':
                               product_item = sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids)[0]
                               total_linear_meter = (quantity or 0.0) * product_item['linear_length']
                               total_volume = (quantity or 0.0) * (product_item['volume'] or 0.0)
                               total_weight = (quantity or 0.0) * (product_item['weight'] or 0.0)
                           else: # description line
                               total_linear_meter = False 
                               total_volume = False 
                               total_weight = False 

                               if line_type == "a": 
                                  raise_error("[ERR] Riga:%s - Prodotto non trovato: %s"%(counter['tot'], articolo_id), out_file)
                           
                           total=0 #TODO
                           partner_id = get_partner_id(sock, uid, pwd, mexal_id)

                           if line_type=="a":
                              if not colli:
                                 colli = quantity # se non ci sono i colli metto uguale a quantity (per avere il 20 x 1)
                           if port_code not in ('', 'f', 'a', 'd'):
                              raise_error("[ERR] Riga:%s - Codice Porto non trovato: %s"%(counter['tot'], port_code), out_file)

                           if line_type not in ('a', 'd'):
                              raise_error("[ERR] Riga:%s - Tipo di linea non trovato: %s"%(counter['tot'], line_type), out_file)
                              
                           if not partner_id:
                              raise_error("[ERR] Riga:%s - Partner non trovato: %s"%(counter['tot'], mexal_id), out_file)

                           if type_of_line.lower() == 'b':
                              quantity_ok = quantity or 0.0
                           else:
                              quantity_ok = 0.0
                               
                           if not number:   
                              raise_error("[ERR] Riga:%s - Numero d'ordine non trovato: %s"%(counter['tot'], number), out_file)
                              
                           # Inserimento ordine testata statistic.header
                           if old_order_number != number: # se cambia faccio le verifiche o lo creo altrimenti rimane l'ID prec.
                               old_order_number = number # memorizzo il vecchio numero
                               counter['order']+=1
                               sequence = 1
                               header = {'name': number, #"Ordine n.:%s"%(number,),
                                         'partner_id': partner_id,
                                         'date': order_date,
                                         'deadline': order_deadline,
                                         #'total': fields.float('Total', digits=(16, 2)),
                                         'note': note,
                                         'port_code': port_code,
                                         'port_description':port_description,
                                         'destination':destination_description,
                                         'destination_address': destination_address,
                                         'destination_cap': destination_cap,
                                         'destination_country': destination_loc,
                                         'destination_prov': destination_prov,
                                         'agent_description': agent_description,
                                         # extra window:
                                         
                                         'registration_date': registration_date,
                                         'extra_note': extra_note,                                 
                                        }
                               # TODO ottimizzabile cercando la rottura di codice:       
                               search_header_id = sock.execute(dbname, uid, pwd, 'statistic.header', 'search', [('name','=',number)])
                               if search_header_id:
                                  header_id=search_header_id[0] # Memorizzo per associarlo poi all'ordine
                               else: # Creo:
                                   try:
                                      header_id = sock.execute(dbname, uid, pwd, 'statistic.header', 'create', header)
                                   except:
                                      raise_error("[ERR] Riga:%s - Errore creando header: %s"%(counter['tot'], number), out_file)
                                   if verbose: 
                                      raise_error("[INFO] Riga:%s - Header inserito: %s"%(counter['tot'], number), out_file)
                           else: # stesso ordine
                               sequence += 1

                           # Inserimento dettaglio ordine  (associando la riga con l'header_id)
                           # Importazione dato: statistic.order
                           data={'name': number,
                                 'partner_id': partner_id,
                                 'date': order_date,
                                 'deadline': order_deadline,
                                 'total': total,
                                 'code': articolo_id, # codice di mexal
                                 'article': "%s %s"%(articolo,product_description), # descrizione articolo + descrizione italiana aggiuntiva
                                 'quantity': quantity,
                                 'quantity_ok': quantity_ok,
                                 'total_linear_meter': total_linear_meter,
                                 'total_volume': total_volume,
                                 'total_weight': total_weight,
                                 'note':note,                         
                                 'header_id': header_id, 
                                 'line_type': line_type,
                                 'colli': colli,
                                 'sequence': sequence,
                                 }
                           
                           if not order_deadline and line_type=="a": # Comunico solo nel caso non sia riga descrittiva 
                              raise_error("[ERR] Riga:%s - Scadenza non trovata: %s"%(counter['tot'], number), out_file)
                           elif order_deadline:
                              mod_response = sock.execute(dbname, uid, pwd, 'statistic.header', 'write', header_id, {'deadline': order_deadline,}) # TODO optimize! <<<<<<<<<<<
                              

                           if type_of_line:
                              data['type']= type_of_line.lower()

                           try:
                             order_id = sock.execute(dbname, uid, pwd, 'statistic.order', 'create', data)  
                           except:
                              raise_error("[ERR] Riga:%s - Errore creando ordine: %s"%(counter['tot'], number), out_file)
                           
                           if verbose: 
                              raise_error("[INFO] Riga:%s - Ordine inserito: %s"%(counter['tot'], number), out_file)

                       except:
                           raise_error("[ERR] Riga:%s - Errore di importazione: %s"%(counter['tot'],  sys.exc_info()[0]), out_file)
                   else:
                           raise_error("[ERR] Riga:%s - Riga vuota o con colonne diverse: file %s, riga %s"%(counter['tot'], tot_col, len(line)), out_file)
        except:
            raise_error("[ERR] Errore importando gli ordini!", out_file)
            raise 
        raise_error("[INFO] Totale ordini: %s  -  Totale righe: %s"%(counter['order'],counter['tot'],), out_file)

        if debug_mode: # Parte comune a tutte le procedure:
            file_log=os.path.abspath(os.path.dirname(FileInput))+"/log.FIA"
            raise_error("\n\n[DEBUG] Date files importati:", out_file)      
            i=0
            for line in open(file_log,'r'):
               i+=1
               if i>7: # jump first line (description and . / ..)
                  if line and line[0:1]!=" ":
                     raise_error("\tData: %s - File: %s"%(line[0:17], line[35:].strip(),), out_file)






    def to_print(self, cr, uid, ids, context=None):
        header_mod=self.write(cr, uid, ids, {'print': True}, context=context)
        return True

    def no_print(self, cr, uid, ids, context = None):
        header_mod=self.write(cr, uid, ids, {'print': False}, context=context)
        return True

    def _function_order_header_statistic(
            self, cr, uid, ids, field_name, arg, context=None):
        """ Calcola i campi statistici nell'ordine
        """
        if context is None:
           context = {}

        res = {}
        for header in self.browse(cr, uid, ids, context=context):
            res[header.id] = {}
            res[header.id]['complete'] = True # initial value
            res[header.id]['total_item'] = 0.0
            res[header.id]['total_item_complete'] = 0.0
            res[header.id]['total_linear_meter'] = 0.0
            res[header.id]['total_linear_meter_ready'] = 0.0
            res[header.id]['total_volume'] = 0.0
            res[header.id]['total_volume_ready'] = 0.0
            res[header.id]['total_weight'] = 0.0
            for line in header.line_ids:
                res[header.id]['total_item'] += line.quantity or 0.0
                res[header.id][
                    'total_item_complete'] += line.quantity_ok or 0.0
                res[header.id][
                    'total_linear_meter'] += line.total_linear_meter or 0.0
                res[header.id][
                    'total_volume'] += line.total_volume or 0.0
                res[header.id][
                    'total_weight'] += line.total_weight or 0.0

                # test only A(rticle) line
                if line.line_type=='a' and not line.type=='b':
                    res[header.id]['complete'] = False

                if line.type=='b':
                   res[header.id][
                       'total_linear_meter_ready'] += line.total_linear_meter \
                           or 0.0
                   res[header.id][
                       'total_volume_ready'] += line.total_volume or 0.0
        return res


    _columns = {
        'name': fields.char('Numero ordine', size=16),
        'visible': fields.boolean('Visible',),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)), # TODO calcolato
        'note': fields.char('Note', size=64),
        'print': fields.boolean('To print'),

        'registration_date': fields.date('Registration date'),
        'extra_note': fields.char('Extra Note', size=64),

        'agent_description': fields.char('Agent description', size=36),

        'property_account_position': fields.related(
            'partner_id', 'property_account_position', type='many2one',
            relation='account.fiscal.position', store=True,
            string='Fiscal position'),
        'country_id': fields.related(
            'partner_id', 'country', type='many2one', relation='res.country',
            string='Country', store=True),
        'zone_id': fields.related(
            'partner_id', 'zone_id', type='many2one',
            relation='res.partner.zone', string='Zona', store=True),

        'line_ids': fields.one2many(
            'statistic.order', 'header_id', 'Linee dettaglio'),

        # Campi funzione:
        'complete': fields.function(
            _function_order_header_statistic, method=True, type='boolean',
            string='Completo', multi="statistiche", store=False),
        'total_item': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='N. art.', multi="statistiche",
            store=False),
        'total_item_complete': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='N. Art. (pronti)', multi="statistiche",
            store=False),
        'total_linear_meter': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Mt. lineari', multi="statistiche",
            store=False),
        'total_linear_meter_ready': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Mt. lineari (pronti)', multi="statistiche",
            store=False),
        'total_volume': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Volume', multi="statistiche", store=False),
        'total_volume_ready': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Volume (pronto)', multi="statistiche",
            store=False),
        'total_weight': fields.function(
            _function_order_header_statistic, method=True, type='float',
            digits=(16, 2), string='Peso', multi="statistiche", store=False),

        'port_code': fields.selection([
            ('f','Franco'),
            ('a','Assegnato'),
            ('d','Addebito'),
            ], 'Port'),
        'port_description': fields.char('Port description', size=40),
        'destination': fields.char('Destination ', size=40),
        'destination_address': fields.char('Destination address ', size=40),
        'destination_cap': fields.char('Destination cap', size=40),
        'destination_country': fields.char('destination country', size=40),
        'destination_prov': fields.char('destination province', size=40),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
