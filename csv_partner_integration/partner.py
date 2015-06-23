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

class ResPartner(orm.Model):
    ''' Add scheduled operations
    '''
    _inherit = 'res.partner'

    # -------------------------------------------------------------------------
    #                          Utility function:
    # -------------------------------------------------------------------------
    def get_statistic_category(self, cr, uid, category, context=None):
        ''' Get (or create) statistic category (obj: statistic.category)
        '''
        if category:
            return False
            
        category = category.strip()
        category = category.capitalize()        
        category_pool = self.pool.get('statistic.category')
        item_ids = category_pool.search(cr, uid, [
            ('name', '=', category)], context=context)
        if item_ids:
           return item_ids[0]
        else:
           return category_pool.create(cr, uid, {
               'name': category,
               }, context=context)

    def get_zone(self, cr, uid, zone, context=None):
        ''' Get (or create) zone element (obj: res.partner.zone)
        '''
        if not zone:
            return False
            
        zone = zone.strip()
        zone = zone.capitalize()        
        zone_pool = self.pool.get('res.partner.zone')
        item_ids = zone_pool.search(cr, uid, [
            ('name', '=', zone)], context=context)
        if item_ids:
           return item_ids[0]
        else:
           return zone_pool.create(cr, uid, {
               'name': zone,
               }, context=context)
    
    def get_agent(self, cr, uid, ref, name, context=None):
        ''' Test if there's ref agent in static.invoice.agent
            1. False: Create and return ID
            2. True: Get and return ID
        '''
        if not ref:
            return False
            
        agent_pool = self.pool.get('statistic.invoice.agent')    
        item_ids = agent_pool.search(cr, uid, [
            ('ref', '=', ref)], context=context) 
        if item_ids:
            return item[0]
        else:
            return agent_pool.create(cr, uid, {
                'ref': ref, 
                'name': name, 
                }, context=context) 

    def load_fiscal_position(self, cr, uid, fiscal_position_list, context=None):
        ''' In accounting there's 3 position: C, E, I
            Load the fiscal_position_list dictionary 
        '''
        fiscal_pool = self.pool.get('account.fiscal.position')
        
        fiscal_ids = fiscal_pool(cr, uid, [], context=context)
        fiscal_proxy = fiscal_pool.proxy(cr, uid, fiscal_ids, context=context)
        for item in fiscal_proxy:
            if item.name == 'Regime Intra comunitario':
               fiscal_position_list['c'] = item.id
            elif item.name == 'Regime Extra comunitario':
               fiscal_position_list['e'] = item.id
            elif item.name == 'Italia':
               fiscal_position_list['i'] = item.id
        return

    def parse_discount(self, discount):
        ''' Parse string for discount and calculate real float
        '''
        res = {}
        discount = discount.strip()
        discount = discount.replace(",",".")
        discount_list = discount.split('+')
        if len(discount_list): #
           base_discount = 100.00
           for r in discount_list:
               try: 
                   i = float(r)
               except:
                   i = 0.00
               base_discount -= base_discount * i / 100.00 
           res['value'] = 100 - base_discount
           res['rates']= '+'.join(discount_list)
        else:
           res['value'] = 0
           res['rates'] = ''
        return res

    # -------------------------------------------------------------------------
    #                      Scheduled function for import:
    # -------------------------------------------------------------------------
    def schedule_csv_partner_integration(self, cr, uid,
            customer_file='~/ETL/copenerp.csv', 
            supplier_file='~/ETL/fopenerp.csv',
            delimiter=';', header_line=0,
            verbose=100, context=None):
        ''' Import partner extra fields, this operation override sql schedule
            for add extra fields that could not be reached fast
        '''
        _logger.info('Start partner integration, file: %s' % input_file)
        
        # Customer integration
        

        pricelists = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        #ReadAllPricelist(sock, dbname, uid, pwd, range(0,10), pricelists)
        fiscal_position_list = {}
        self.load_fiscal_position(
            cr, uid, fiscal_position_list, context=context)
        # client_list = cPickleParticInput(file_name_pickle) << TODO partic for pl
        
        # Default elements:
        type_address = 'default'
        type_address_destination = 'delivery'
        csv_pool = self.pool.get('csv.base')

        loop = [
            ('c', False, customer_file), # customer only
            ('c', True, customer_file),  # customer destination only
            ('s', False, supplier_file),  # supplier only
            ('s', True, supplier_file),  # supplier destination only            
            ]
        
        # 4 loop for complete importation:    
        for mode, is_destination, input_file in loop:    
            _logger.info('Start import %s element %s' % (
                'customer' if mode == 'c' else 'supplier,
                'destination' if is_destination else 'parent',))

            counter = 0
            tot_col = 0        
            lines = csv.reader(
                open(input_file, 'rb'), delimiter=delimiter)

            for line in lines:
                try:
                    # Jump header lines:
                    if counter < 0:
                       counter += 1
                       continue

                    counter += 1
                    # Jump empty lines:
                    if not len(line): 
                        _logger.warning('%s. Jump empty line' % counter)
                        continue

                    # Read total of columns:
                    if not tot_col:
                        tot_col = len(line)
                        _logger.info('Total columns: %s' % tot_col)
                       
                    # Jump lines with different cols:    
                    if tot_col != len(line): 
                        _logger.error('%s. Line with different cols [%s > %s]' % (
                            counter,
                            tot_col,
                            len(line), )
                       continue     
                            
                    ref = csv_pool.decode_string(line[0])
                    name = csv_pool.decode_string(line[1]).title()
                    first_name = csv_pool.decode_string(line[2]).title()
                    street = csv_pool.decode_string(line[3]).title()
                    zipcode = csv_pool.decode_string(line[4])
                    city = csv_pool.decode_string(line[5]).title()
                    prov = csv_pool.decode_string(line[6]).upper()
                    phone = csv_pool.decode_string(line[7])
                    fax = csv_pool.decode_string(line[8])
                    email = csv_pool.decode_string(line[9]).lower()
                    fiscal_code = csv_pool.decode_string(line[10]).upper()
                    vat = csv_pool.decode_string(line[11]).upper() # IT* format
                    type_CEI = csv_pool.decode_string(line[12]).lower() #  C, E, I 
                    code = csv_pool.decode_string(line[13]).upper() # Verify "IT" 
                    private = csv_pool.decode_string(line[14]).upper()=="S"
                    parent = csv_pool.decode_string(line[15]) # partner partner
                    ref_agente = csv_pool.decode_string(line[16]) # ID agente
                    name_agente = csv_pool.decode_string(line[17]).title()
     
                    # Get ID for agent name:
                    agent_id = False
                    # TODO verify for suppliers and destination!!!
                    pl_version = 0
                    
                    # TODO:
                    if (mode == 'c') and (not is_destination) and ref_agente[:2] not in ('05', '20',): # Pricelist only present for client TODO not destination                       
                        agent_id = self.get_agent(cr, uid, ref_agente, name_agente)
                        
                        # 10 pricelist standard:
                        pl_code = csv_pool.decode_string(line[18])
                        if pl_code:
                            try:
                                pl_version = int(pl_code)   
                            except:                           
                                _logger.error('Pricelist code error: %s' % pl_code)
     
                    discount = csv_pool.decode_string(line[19]) # Discount list
                    if discount:
                        discount = discount.replace(
                            "+", "+ ").replace(
                            "  ", " ")
                    esention_code = csv_pool.decode_string(line[20])
                    country_code = csv_pool.decode_string(line[21]).upper()
                    fido_total = csv_pool.decode_float(line[22])
                    fido_date = csv_pool.decode_date(line[23]) # FIDO from date 
                    fido_ko = ('x' == csv_pool.decode_string(line[24])) # X = loose
                    # 25 = ID zone (accounting)
                    zone = csv_pool.decode_string(line[26])
                    zone_id = self.get_zone(cr, uid, ids, zone)
     
                    # TODO only 1 company used it:
                    if tot_col > 27:
                        # 27 ID category               
                        category = csv_pool.decode_string(line[28]) # Stat. categ.
                        category_id = self.get_statistic_category(
                            cr, uid, category, context=context)
                        ddt_e_oc = csv_pool.decode_float(line[29]) # balance accoun.

                    else:
                        category_id = False
                        ddt_e_oc = ""

                    pricelist_id=0
                    # TODO rivedere!!!
                    """
                    if pl_version in range(1,10): # version [1:9]
                        if ref in client_list:
                            result = {} 
                            GetPricelist(sock, dbname, uid, pwd, ref, pl_version, pricelists[pl_version], result) # 2 returned values in dict
                            pricelist_id = result['pricelist']
                        else: # Link to standard PL version
                            pricelist_id = pricelists[pl_version]
                    else:
                        pricelist_id=0
                    """
     
                    discount_parsed = parse_discount(discount)               

                    # TODO rivedere:
                    """
                    if is_destination:  # TODO with ^ XOR
                       if not parent: # Destination have parent field
                          if verbose: print "[INFO]", "JUMPED (not a destination)",ref,name
                          continue # jump if is destination and record is c or s
                    else: # c or s 
                       if parent: 
                          if verbose: print "[INFO]", "JUMPED (not a client / supplier)",ref,name
                          continue # jump if is c or s but parent is present
                    """
                    if type_CEI in ('c', 'e', 'i', 'v', 'r'):
                        fiscal_position = fiscal_position_list.get(type_CEI, 'e')
                    else:
                       fiscal_position = False
                       _logger.error("Field C, E, I with wrong code: %s" % type_CEI
     
                    # Calculated fields:    
                    if first_name: 
                        name += " " + first_name
                    if prov: 
                        city += " (%s)" % prov
                       
                    # TODO:
                    # lang_id = getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")    # TODO check in country (for creation not for update)

                    # Default data dictionary (to insert / update)
                    data_address = {
                        'city': city, # modify first import address
                        'zip': zipcode, 
                        #TODO 'country_id': getCountryFromCode(sock,dbname,uid,pwd,country_code), 
                        'phone': phone,
                        'fax': fax,
                        'street': street, 
                        'import': True,
                        #'email': email
                        #'type': type_address,
                        }    
                    if not is_destination: # create partner only with c or s
                        data = {
                            'name': name,
                            'fiscal_id_code': fiscal_code, 
                            'phone': phone,
                            'email': email, 
                            'lang_id': lang_id,
                            'vat': vat,
                            #'category_id': [(6,0,[category_id])], # m2m
                            #'comment': comment, # TODO create list of "province" / "regioni"
                            'mexal_' + mode : ref,
                            'discount_value': discount_parsed['value'],
                            'discount_rates': discount_parsed['rates'],                             
                            'import': True,                    
                            'fido_total': fido_total,
                            'fido_date': fido_date,
                            'fido_ko': fido_ko,  
                            'zone_id': zone_id,                              
                            }

                        if azienda == "fiam" and mode == 'c':  # Per ora solo per la fiam
                            data['statistic_category_id'] = category_id
                            if agent_id:
                                data['invoice_agent_id'] = agent_id

                        if mode == 'c': # and not destination!                       
                            data['property_product_pricelist']= pricelist_id  
                            data['property_account_position']= fiscal_position
                            data['customer']=True
                            data['ref']=ref
                            data['type_cei']=type_CEI
                            data['ddt_e_oc_c']=ddt_e_oc
                           
                        if mode == 's': 
                            data['supplier']=True
                            data['ddt_e_oc_s']=ddt_e_oc
     
                        data_address['type']=type_address  # default
                    else:  # destination
                        data_address['mexal_' + mode]= ref      # ID in address
                        data_address['type']= type_address_destination # delivery
                   
                    # PARTNER CREATION ***************
                    if not is_destination:  # partner creation only for c or s
                        error="Searching partner with ref"
                        item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_' + mode, '=', ref)]) # search if there is an import
                        if (not item): # partner not found with mexal_c, try with vat  <<<< TODO problem 2 client with same vat!!!
                            if vat:
                                item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('vat', '=', vat),('mexal_' + mode, '=', False)]) # search if there is a partner with same vat (c or f)
                                if not item and mode == "s":
                                   data['customer'] = False
                            else:
                                if mode == "s":
                                    data['customer'] = False
     
                        error_print = "Partner not %s: [%s] %s (%s)"
                        if item: # modify
                            counter['upd'] += 1  
                            error="Updating partner"
                            try:
                                item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                                partner_id=item[0] # save ID for address creation
                            except:
                                try: 
                                    del data['vat']    
                                    item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                                    partner_id=item[0] # save ID for address creation
                                except: 
                                    raise_error(error_print % ("modified", data['mexal_' + mode], data['name'], ""), out_file, "E")
                                    counter['err_upd']+=1  
                                    #raise # << don't stop import process

                            if verbose: print "[INFO]", counter['tot'], "Already exist: ", ref, name
                        else: # create
                            counter['new'] += 1  
                            error="Creating partner"
                            try:
                                partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                                #except ValidateError:
                                #   print "[ERROR] Create partner, (record not writed)", data                          
                            except:
                                try: 
                                    del data['vat']    
                                    partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                                except: 
                                    raise_error(error_print % ("created",data['mexal_' + mode],data['name'], ""), out_file, "E")
                                    counter['err']+= 1  
                                    #raise # << don't stop import process
     
                            if verbose: 
                                print "[INFO]", counter['tot'], "Insert: ", ref, name
                    else: # destination
                        partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_' + mode, '=', parent),])
                        if partner_id: 
                            #print "**", partner_id
                            partner_id=partner_id[0] # only the first
                          
                   
                    if not partner_id:  
                        raise_error('No partner [%s] rif: "%s" << [%s] ' % (mode, ref, parent),out_file,"E")
                        continue # next record

                    # ADDRESS CREATION ***************
                    error = "Searching address with ref"
                    if is_destination:   
                        item_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('import', '=', 'true'),('type', '=', type_address_destination),('mexal_' + mode, '=', ref)]) # TODO error (double dest if c or s)
                    else:   
                        item_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('import', '=', 'true'),('type', '=', type_address),('partner_id','=',partner_id)])
                    counter['tot_add'] += 1

                    if item_address:
                        counter['upd_add'] += 1  
                        error = "Updating address"
                        try:
                            item_address_mod = sock.execute(dbname, uid, pwd, 'res.partner.address', 'write', item_address, data_address) 
                        except:
                            print "     [ERROR] Modifing address, current record:", data_address
                            raise # eliminate but raise log error
                       if verbose: print "     [INFO]", counter['tot_add'], "Already exist address: ", ref, name
                    else:           
                        counter['new_add'] += 1  
                        error="Creating address"
                        try:
                            data_address['partner_id']=partner_id # (only for creation)
                            item_address_new=sock.execute(dbname, uid, pwd, 'res.partner.address', 'create', data_address) 
                        except:
                            raise_error("Insert data, current record:" + str(data),out_file,"E")
                        if verbose: print "     [INFO]",counter['tot_add'], "Insert: ", ref, name
                 else: # wrong column number
                     counter['err']+=1
                     raise_error('Line %d (sep.: "%s"), %s)' % (counter['tot'] + 1 ,separator, line[0].strip() + " " +line[1].strip()),out_file,"C")
     
                 except:
                     raise_error ('>>> Import interrupted! Line:' + str(counter['tot']),out_file,"E")
                     if verbose_mail: 
                       send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)
                     raise # Exception("Errore di importazione!") # Scrivo l'errore per debug
 
        print "[INFO]","Address:", "Total line: ",counter['tot_add']," (imported: ",counter['new_add'],") (updated: ", counter['upd_add'], ")"
        
        # Supplier integration
        
        # Destination integration
        
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
