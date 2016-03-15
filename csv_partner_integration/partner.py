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
        if not category:
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
            return item_ids[0]
        else:
            return agent_pool.create(cr, uid, {
                'ref': ref,
                'name': name,
                }, context=context)

    def load_fiscal_position(self, cr, uid, fiscal_position_list, 
            context=None):
        ''' In accounting there's 3 position: C, E, I
            Load the fiscal_position_list dictionary
        '''
        fiscal_pool = self.pool.get('account.fiscal.position')

        fiscal_ids = fiscal_pool.search(cr, uid, [], context=context)
        for item in fiscal_pool.browse(cr, uid, fiscal_ids, context=context):
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
        discount = discount.replace(",", ".")
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

    def read_all_pricelist(self, cr, uid, pricelists, context=None):
        ''' Read all pricelist version
        '''
        pl_pool = self.pool.get('product.pricelist')
        pl_ids = pl_pool.search(cr, uid, [
            ('mexal_id', '!=', False)], context=context)
        for item in pl_pool.browse(cr, uid, pl_ids, context=context):
            pricelists[item.mexal_id] = item.id
        return

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
        _logger.info('Start partner integration.')

        # ---------------------------------------------------------------------
        # Pricelist importation:
        # ---------------------------------------------------------------------
        
        
        # ---------------------------------------------------------------------
        # Partner importation (customer, cust. dest, supplier, supp. dest):
        # ---------------------------------------------------------------------
        # Read all pricelist version:
        pricelists = {}
        self.read_all_pricelist(cr, uid, pricelists, context=context)
        
        fiscal_position_list = {}
        self.load_fiscal_position(
            cr, uid, fiscal_position_list, context=context)
        # client_list = cPickleParticInput(file_name_pickle) << TODO partic for pl

        # Default elements:
        type_address = 'default'
        type_address_destination = 'delivery'
        csv_pool = self.pool.get('csv.base')

        loop = [
            ('customer', False, customer_file), # customer only
            #('customer', True, customer_file),  # customer destination only # TODO
            #('supplier', False, supplier_file),  # supplier only
            #('supplier', True, supplier_file),  # supplier destination only
            ]

        # 4 loop for complete importation:
        for mode, is_destination, input_file in loop:
            _logger.info('Start import %s element %s' % (
                mode,
                'destination' if is_destination else 'parent',))

            counter = 0
            tot_col = 0
            lines = csv.reader(
                open(os.path.expanduser(input_file), 'rb'), 
                delimiter=delimiter)

            for line in lines:
                try:
                    # Jump header lines:
                    if counter < 0:
                       counter += 1
                       continue

                    counter += 1

                    if verbose and counter and counter % verbose == 0:
                        _logger.info('Record updated: %s' % counter)
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
                        _logger.error('%s. Different cols [%s > %s]' % (
                            counter, tot_col, len(line), 
                            ))
                        continue
                        
                    # Read all fields to import:
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
                        
                    type_CEI = csv_pool.decode_string(line[12]).lower()
                    if type_CEI in ('c', 'e', 'i', 'v', 'r'):
                        if type_CEI in ('v', 'r'):
                            type_CEI = 'e'
                        fiscal_position = fiscal_position_list.get(
                            type_CEI, False)
                    else:
                       fiscal_position = False
                       _logger.error("Field C, E, I with wrong code: %s" % (
                           type_CEI))

                    code = csv_pool.decode_string(line[13]).upper() # IT
                    private = csv_pool.decode_string(line[14]).upper() == "S"
                    parent = csv_pool.decode_string(line[15]) # partner partner
                    ref_agente = csv_pool.decode_string(line[16]) # ID agente
                    name_agente = csv_pool.decode_string(line[17]).title()

                    # Pricelist only present for client 
                    if (mode == 'customer') and (not is_destination): 
                        # and ref_agente[:2] not in ('05', '20',): TODO serve?
                        agent_id = self.get_agent(
                            cr, uid, ref_agente, name_agente, context=context)

                        # 10 pricelist default:
                        pl_version = csv_pool.decode_string(line[18]) or False
                        ref_pricelist_id = pricelists.get(pl_version, False)
                        # TODO change for remove customer PL
                        pricelist_id = pricelists.get(ref, ref_pricelist_id)
                        #pricelist_id = ref_pricelist_id # <<<<<
                        # mette il listino di riferimento corretto!!!!!!!!!!!!!
                    else:
                        agent_id = False
                        pl_version = False
                        ref_pricelist_id = False
                        pricelist_id = False
    
                    discount = csv_pool.decode_string(line[19]) # Discount list
                    if discount:
                        discount = discount.replace(
                            "+", "+ ").replace(
                            "  ", " ")
                    discount_parsed = self.parse_discount(discount)

                    esention_code = csv_pool.decode_string(line[20])
                    country_code = csv_pool.decode_string(line[21]).upper()
                    fido_total = csv_pool.decode_float(line[22])
                    fido_date = csv_pool.decode_date(line[23]) # FIDO from date
                    fido_ko = ('x' == csv_pool.decode_string(line[24])) # X=no
                    # 25 = ID zone (accounting)
                    zone = csv_pool.decode_string(line[26])
                    zone_id = self.get_zone(
                        cr, uid, zone, context=context)

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
                        'mexal_province': prov,
                        #'email': email
                        #'type': type_address,
                        }

                    if is_destination: # create partner only with c or s
                        data_address['sql_%s_code' % mode] = ref      # ID in address
                        data_address['type'] = type_address_destination # delivery
                    else:    
                        data = {
                            #NO 'name': name,
                            #NO 'fiscal_id_code': fiscal_code,
                            #NO 'phone': phone,
                            #NO 'email': email,
                            #NO 'lang_id': lang_id,
                            #NO 'sql_%s_code' % mode : ref,
                            #NO 'vat': vat, # for deletion
                            'discount_value': discount_parsed['value'],
                            'discount_rates': discount_parsed['rates'],
                            #NO 'import': True,
                            'fido_total': fido_total,
                            'fido_date': fido_date,
                            'fido_ko': fido_ko,
                            'zone_id': zone_id,
                            
                            #'category_id': [(6,0,[category_id])], # m2m
                            #'comment': comment, 
                            # TODO create list of "province" / "regioni"
                            }

                        # Only customer
                        if mode == 'customer':  # TODO era solo per company1
                            data['statistic_category_id'] = category_id                            
                            if agent_id:
                                data['invoice_agent_id'] = agent_id
                                
                            # TODO parte comune per tutti i clienti:
                            data['property_product_pricelist'] = pricelist_id
                            data['ref_pricelist_id'] = ref_pricelist_id
                            #data['property_account_position'] = fiscal_position 
                            # NOTE: Imported with sql_partner!!!
                            #NO data['customer'] = True
                            #NO data['ref'] = ref
                            data['type_cei'] = type_CEI
                            data['ddt_e_oc_c'] = ddt_e_oc

                        if mode == 'supplier':
                            #NO data['supplier'] = True
                            
                            data['ddt_e_oc_s'] = ddt_e_oc

                        data_address['type'] = type_address  # default

                    if is_destination:  # partner creation only for c or s
                        partner_ids = self.search(cr, uid, [
                            ('sql_%s_code' % mode, '=', parent)
                            ], context=context)
                        if partner_ids:
                            partner_id = partner_ids[0] # only the first
                    else: # partner
                        item_ids = self.search(cr, uid, [
                            ('sql_%s_code' % mode, '=', ref)], context=context)
                        # partner not found with 'sql_customer_code', 
                        # try with vat  <<<< TODO problem 2 client w/same vat!!
                        """if not item_ids: 
                            if vat:
                                item_ids = self.search(cr, uid, [
                                    ('vat', '=', vat),
                                    ('sql_%s_code' % mode, '=', False)
                                    ], context=context)
                                if not item_ids and mode == 'supplier':
                                   data['customer'] = False
                            else:
                                if mode == 'supplier':
                                    data['customer'] = False"""

                        if item_ids: # modify
                            #try:
                            partner_id = item_ids[0]
                            self.write(cr, uid, item_ids, data, context=context)
                            #except: # if error go to master error in loop:
                            """ del data['vat']
                                partner_id = item_ids[0]
                                self.write(
                                    cr, uid, partner_id, data, context=context)
                                """

                        else: # create
                            #try:
                            continue # TODO not created only updated
                            """ partner_id = self.create(
                                    cr, uid, data, context=context)
                            except: # if error go to master error in loop:
                                del data['vat']
                                partner_id = self.create(
                                    cr, uid, data, context=context)
                            """

                    if not partner_id:
                        _logger.error('No partner [%s] rif: "%s" << [%s] ' % (
                            mode, ref, parent))
                        continue # next record

                    # ADDRESS CREATION ***************
                    # TODO
                    """if is_destination:
                        # TODO Duplication if same in c or s
                        item_address = self.search(cr, uid, [
                            ('is_address', '=', 'true'), # TODO remove
                            ('type', '=', type_address_destination),
                            ('sql_%s_code' % mode, '=', ref)
                            ], context=context)
                    else:
                        item_address = self.search(cr, uid, [
                            ('is_address', '=', 'true'),
                            ('type', '=', type_address),
                            ('partner_id','=',partner_id)
                            ], context=context)

                    if item_address:
                        self.write(
                            cr, uid, item_address, data_address, 
                            context=context)
                    else:
                        data_address['partner_id'] = partner_id # only creation
                        item_address_new = self.create(
                            cr, uid, data_address, context=context)
                    """

                except:
                    _logger.error('%s. Error import line: [%s]' % (
                            counter, sys.exc_info(), ))
                    continue

            _logger.info('End of importation, totals line: %s' % counter)
            # TODO caricamento note partner??
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
