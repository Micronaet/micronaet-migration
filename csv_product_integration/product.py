# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
import csv
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

class ProductProduct(orm.Model):
    ''' Add scheduled operations
    '''
    _inherit = 'product.product'

    def schedule_csv_import_note(self, cr, uid, input_file, context=None):
        ''' Import note from mexal file:
            format: NN.NNNNN lNNN
        '''
        def prepare(valore):  
            
            #valore = unicode(valore, 'ISO-8859-1')
            # Windows-cp1252 ISO-8859-1
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            valore=valore.replace("   ","")
            valore=valore.replace("\x00","")  
            valore=valore.replace("-------","-")  
            valore=valore.replace("*******","*")  
            return valore.strip()

        def is_correct_code(MexalCode, LenCode):
            ''' Check format for code (TODO use re)
            '''
            try: 
               numeri="0123456789"
               lettere="abcdefghijklmnopqrstuvwxyz"  
               if len(MexalCode)<>LenCode: 
                  return False
               else:
                  #print "Testing: ", MexalCode  
                  if (MexalCode[0] in numeri) and \
                     (MexalCode[1] in numeri) and \
                     (MexalCode[2] == ".") and \
                     (MexalCode[3] in numeri) and \
                     (MexalCode[4] in numeri) and \
                     (MexalCode[5] in numeri) and \
                     (MexalCode[6] in numeri) and \
                     (MexalCode[7] in numeri) and \
                     (MexalCode[8] == " ") and \
                     (MexalCode[9].lower() in lettere) and \
                     (MexalCode[10] in numeri) and \
                     (MexalCode[11] in numeri) and \
                     (MexalCode[12] in numeri):
                     return True
                  else:
                     return False 
            except: 
               return False # in case of error test failed

        f = open(input_file, 'r')
        total = prepare(f.read())
        note = {}
        code_len = 13

        old_code = ""
        old_i = 0
        for i in range(0, len(total) - cod_len):
            if is_correct_code(total[i : (i + cod_len)], cod_len):
                if old_code: # else is the first record, nothing to write
                    if old_code[:8] in note.keys(): # TODO is present?
                       note[old_code[:8]] = "%s\n%s) %s" % (
                           note[old_code[:8]],
                           old_code[8:],
                           total[old_i:i].strip()
                           )
                    else:
                       note[old_code[:8]] = "%s) %s" % (
                           old_code[8:],
                           total[old_i:i].strip()
                           )
                    old_code = total[i: (i + old_code)] # Actual begin old          
                else:
                    old_code = total[i: (i + old_code)]
                    old_i = i
                old_i = i + old_code # save actual i + len of code for value 
                i += old_code # jump len code char

        partner_pool = self.pool.get('res.partner')
        for key in note.keys():            
            partner_ids = partner_pool.search(cr, uid, [
                ('sql_customer_code', '=', key[:8])])
            if partner_ids:
                partner_pool.write(cr, uid, partner_ids, {
                    'mexal_note': '[Agg.: %s] %s' % (
                        datetime.today().strftime('%Y-%m-%d'),
                        note[key], )
                    })
            else:
                _logger.error("Partner not found: %s" % key[8:])

    def schedule_csv_group_force(self, cr, uid, context=None):        
        ''' Force group (custom for a particular client)        
        '''
        # TODO remove, not used (with family)
        return True # TODO <<< stop the procedure here!
        product_group = {
            'Prodotti': {
                'Amaca': ('Amaca','Amache',),
                'Appendiabiti': ('Appendiabito', 'Appendiabiti'),
                'Bauli': ('Baule','Bauli',),
                'Birrerie': ('Birreri',),
                'Brandine': ('Brandin',),
                'Cantinette': ('Cantinett', ' Botte', ' Botti', 'Botti ', 
                    'Botte '),
                'Carrelli': ('Carrell',),
                'Chaise Longue': ('Chaise Longue',),
                'Cuscini': ('Cuscin', 'Poggiatest',),
                'Copriruota': ('Copriruota',),
                'Divani': ('Divan',), # C'è dondolina che è una sdraio
                'Dondoli': (' Dondol', 'Dondolo', 'Dondoli '),#dondolina=sdraio
                'Fioriere': ('Fiorier',),
                'Gazebo': ('Gazebo',),
                'Lettini': ('Lettin',),
                'Materassini': ('Materassin',),
                'Ombrelloni': ('Ombrellon', 'Ombr.',),
                'Ottomane': ('Ottoman',),
                'Panca': ('Panca','Panche', 'Cassapanc',),
                'Parasole': ('Parasole ', ' Parasole'),
                'Paraventi': ('Paravent', ),
                'Pergole': ('Pergol',), # Pergole Pergolina Pergoline Pergolato
                'Porta-Cd': ('Porta-Cd',),
                'Poltrone': ('Poltron',), # Poltrone, Poltroncina
                'Prolunghe': ('Prolung',),
                'Sofa': ("Sofa'", ),
                'Schienali': ('Schienal',),
                'Sedie': ('Sedia', 'Sedie', ),
                'Sdraio': ('Sdraio', 'Sedia Sdraio'),
                'Sedili': ('Sedile', 'Sedili', ),
                'Separe': ("Separe'", ),
                'Sgabelli': ('Sgabell', 'Poggiapied'),
                'Spiaggine': ('Spiaggin', ),
                'Strutture': ('Struttur', ),
                'Tavoli': ('Tavol', ),
                }, 
            'Materie prime': {
                'Accessori': ('Accessori', ),
                'Aghi': ('Aghi', ),
                'Angolari': ('Angolar', ),
                'Aste': ('Aste', 'Asta', 'Astin', ),
                'Barre': ('Barra','Barre', ),
                'Banner': ('Banner', ),
                'Blocchetti': ('Blocchett', ),
                'Braccioli': ('Braccioli ', 'Bracciolo '), # 'Sedia con b.'
                'Bussoline': ('Bussolin',),
                'Bobine': ('Bobina', 'Bobine'),
                'Bordini': ('Bordin', ),
                'Bussole': ('Bussol', ),
                'Cartoni': ('Carton', ),
                'Cavalletti': ('Cavallett', ),
                'Cavallotti': ('Cavallott', ),
                'Cellophane': ('Cellophane', ),
                'Cinghie': ('Cinghi', ),
                'Confezioni': ('Confezion', ),
                'Cremagliere': ('Cremaglier', ),
                'Dadi': ('Dadi ','Dado '),
                'Distanziali': ('Distanzial', ),
                'Elastici': (' Elastic', 'Elastico ', 'Elastici '),
                'Etichette': ('Etichett', ),
                'Finta pelle': ('Finta pelle', ), 
                'Fondelli': ('Fondell', ),
                'Gambe': ('Gambe', 'Gamba', 'Gambetta'),
                'Ganci': ('Ganci', ),
                'Manopole': ('Manopole', 'Manopola',),
                'Molle': ('Molle','Molla',),
                'Monoblocchi': ('Monoblocc',),
                'Morsetti': ('Morsett',),
                'Nastro': ('Nastro', 'Nastri',),
                'Perni': ('Perni', 'Perno', ),
                'Piastre': ('Piastr', ),
                'Pinze': ('Pinze','Pinza'),
                'Picchetti': ('Picchett', ),
                'Piani': ('Piani ','Piano ', ),
                'Piatti': ('Piatto ','Piatti ', ),
                'Piedini': ('Piedin', ),
                'Polistirolo': ('Polistirol', ),
                'Polveri': ('Polver', ),
                'Profili': ('Profil', ),
                'Puntali': ('Puntali','Puntale',),
                'Rettangoli': ('Rettangoli', 'Rettangolo'),
                'Ribattini': ('Ribattin', ),
                'Rivetti': ('Rivett', ), 
                'Rondelle': ('Rondell', ),
                'Sacchi': ('Sacchi','Sacco',),
                'Saldature': ('Saldatur',),
                'Scatole': ('Scatol',),
                'Snodi': ('Snodo','Snodi',),
                'Spugne': ('Spugne', 'Spugna'),
                'Staffe': ('Staffe', 'Staffa'),
                'Supporti': ('Support',),
                'Tappi': ('Tappi', 'Tappo',),
                'Telai': ('Telai', 'Telaio',),
                'Teli': ('Tela ','Teli ', 'Tele ','Telo '),
                'Tende': ('Tende', 'Tendaggi',),
                'Tessuti': ('Tessuti', 'Tessuto', 'Texplast', 'Texfil', 
                    'Canapone', 'Juta',),
                'Tondini': ('Tondin', ),
                'Tovagliette': ('Tovagliett', ),
                'Triangoli': ('Triangoli','Triangolo'),
                'Tubi': ('Tubo', 'Tubi', 'Tubolar', 'Tubett'),
                'Vassoi': ('Vassoi', ),
                'Velcri': ('Velcr', ),
                'Verghe': ('Verga', 'Verghe', ),
                'Viti': ('Viti ','Vite '),
                }, 
            'Lavorazioni': {
                'Cromature': ('Cromatur', ),
                'Zincature': ('Zincatur', ),
                'Saldature': ('Saldatur', ),
                },
            'Non classificati': False
            }

        group_pool = self.pool.get('product.group')
        for group in product_group:            
            for item in product_group[group]:
                group_ids = group_pool.search(cr, uid, [
                    ('name', '=', group)], context=context)
                if not group_ids:
                   continue # TODO error
              
                for kw in product_group[group][item]:
                    product_ids = self.search(cr, uid, [
                        ('name', 'ilike', kw)], context=context)
                    self.write(cr, uid, product_ids, {
                        'categ_id': group_ids[0],
                        })  
        return True
 
    def schedule_csv_product_integration(self, cr, uid,
            input_file='~/ETL/artioerp.csv', delimiter=';', header_line=0,
            verbose=100, context=None):
        ''' Import product extra fields, this operation override sql schedule
            for add extra fields that could not be reached fast
        '''
        _logger.info('Start product integration')
        
        # Load UOM:
        uoms = {}   
        uom_failed = []                 
        uom_pool = self.pool.get('product.uom')
        uom_ids = uom_pool.search(cr, uid, []) # no context (english)
        for uom in uom_pool.browse(
                cr, uid, uom_ids, context=context):
            uoms[uom.name] = uom.id

        csv_pool = self.pool.get('csv.base')
        csv_file = open(os.path.expanduser(input_file), 'rb')
        counter = -header_line
        language = {}
        import pdb; pdb.set_trace()
        for line in csv.reader(csv_file, delimiter=delimiter):
            try:
                if counter < 0:  # jump n lines of header
                    counter += 1
                    continue

                if not len(line): # jump empty lines
                    continue

                if verbose and counter and counter % verbose == 0:
                    _logger.info('Product integrated: %s' % counter)
                counter += 1

                # CSV fields:
                default_code = csv_pool.decode_string(line[0])
                uom = csv_pool.decode_string(line[2]).upper()
                #fabric = csv_pool.decode_string(line[18]) # TODO not present!
                
                # TODO move in sql_product CSG_ART_ALT
                ean = csv_pool.decode_string(line[4]).strip()
                if len(ean) != 13 or ean[:2] != '80':
                    ean = False

                # Language:
                name = csv_pool.decode_string(line[1]).title() # it
                language['en_US'] = csv_pool.decode_string(line[11]).title()
                #language['fr_FR'] = csv_pool.decode_string(line[12]).title() # fr
                #language['3'] = csv_pool.decode_string(line[13]).title() # te

                try: # sale lot of product
                    lot = eval(csv_pool.decode_string(
                        line[5]).replace(',', '.'))
                except:
                    lot = 1
                if lot < 0:
                    lot = - lot    
                    
                try:
                    if lot < 1.0:
                        colls = int(0.5 + (1 / lot)) # approx to int 
                    else:
                        colls = 1    
                except:
                    colls = 1    

                # Anagraphic fields:
                linear_length = csv_pool.decode_float(line[14])
                volume = csv_pool.decode_float(line[15])
                weight = csv_pool.decode_float(line[16])

                # Sometimes not present:
                if len(line) > 18:
                    colour = csv_pool.decode_string(line[18]) # TODO lang dec.?
                else:
                    colour = ''

                # Get UOM depend on ref:
                if uom in ['NR', 'N.', 'PZ', 'RT']: 
                    uom_id = uoms.get('Unit(s)', False) # TODO remain unit(s)?
                elif uom in ['M2', 'MQ']: 
                    uom_id = uoms.get('M2', False)
                elif uom in ['M', 'MT', 'ML']: # NOTE: after M2!! 
                    uom_id = uoms.get('m', False)
                elif uom == 'HR': 
                    uom_id = uoms.get('Hour(s)', False)
                elif uom == 'KG': 
                    uom_id = uoms.get('kg', False)
                elif uom == 'LT': 
                    uom_id = uoms.get('Liter(s)', False)
                elif uom == 'KW': 
                    uom_id = uoms.get('KW', False)
                elif uom in ['M3', 'MC']: 
                    uom_id = uoms.get('M3', False)
                elif uom in ['PA', 'CO', 'CP']: 
                    uom_id = uoms.get('P2', False) #pair
                elif uom == 'PC': 
                    uom_id = uoms.get('P10', False)
                elif uom in ['', 'CN', 'MG', 'CM', 'CF', ]: # TODO ??
                    uom_id = uoms.get('Unit(s)', False)
                else: 
                    if uom not in uom_failed:
                        uom_failed.append(uom)
                    uom_id = uoms.get('Unit(s)', False)

                if not uom_id:
                    uom_id = uoms.get('Unit(s)', False)

                product_ids = self.search(cr, uid, [
                    ('default_code', '=', default_code)]) #, context=context)
                    
                data = {
                    'linear_length': linear_length,
                    'weight': weight,
                    'volume': volume,
                    'colour': colour,
                    'q_x_pack': lot,
                    'colls': colls,
                    #'fabric': fabric,
                    #'description_sale': name,
                    #'name_template': name, # TODO langs
                    
                    # Other fields not used: 
                    #'name': name,
                    #'active': active,
                    #'mexal_id': ref,
                    #'import': True,
                    #'sale_ok': True,
                    #'purchase_ok': True,
                    #'default_code': ref,
                    #'type': 'product',
                    #'supply_method': 'produce',
                    #'standard_price': bug_start_value,
                    #'list_price': 0.0,
                    #'procure_method': 'make_to_order',
                    ##'description': description,
                    ##'description_spurchase'
                    ##'lst_price'
                    ##'seller_qty'
                    }
                if ean:
                    data['ean13'] = ean

                if uom_id: 
                    data.update({
                        #'uos_id': uom_id,
                        'uom_id': uom_id,
                        'uom_po_id': uom_id,
                        })
                        
                if product_ids: # only update
                    try: # it_IT
                        self.write(cr, uid, product_ids, data, context=context)
                    except: # update via SQL in case of error
                        _logger.warning('Forced product %s uom %s' % (
                            product_ids[0],
                            uom_id,
                            ))
                        if uom_id: # update via SQL (ODOO not possibile!) 
                            cr.execute(""" 
                                UPDATE product_template
                                SET uom_id = %s, uom_po_id = %s 
                                WHERE id in (
                                    SELECT product_tmpl_id 
                                    FROM product_product
                                    WHERE id = %s);
                                """, (uom_id, uom_id, product_ids[0]))
                            
                    
                    # Update language
                    for lang in language: # extra language
                        name = language.get(lang, False)
                        if name:
                            self.write(cr, uid, product_ids, {
                                'name': name,
                                'description_sale': name,
                                'name_template': name,                                
                                }, context={'lang': lang})

                else:
                    _logger.error('Product not present: %s' % default_code)

            except:
                _logger.error('Product integration %s' % (sys.exc_info(), ))
                continue

        _logger.info('End product integration!')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
