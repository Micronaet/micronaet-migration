# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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
##############################################################################

from osv import osv, fields
class res_company_amazon_migration(osv.osv):    
    ''' Amazon parameter for migration linked to company
    '''
    _name = 'res.company'
    _inherit = 'res.company'

    _columns = {
                'amazon_destination_db': fields.char('DB migration amazon', size=40, required=True, readonly=False, help="Database destination for migrate product"),
                'amazon_destination_db_user': fields.char('DB username', size=40, required=True, readonly=False),
                'amazon_destination_db_password': fields.char('DB password', size=40, required=True, readonly=False),
                'amazon_security_inventory': fields.boolean('Use security level', required=False, readonly=False, help="If true migration of inventory is diminuited of security level of inventory"),
                'amazon_log_mail': fields.char('Amazon log mail', size=80, required=False, readonly=False, help="Mail (separate from comma or semicolon) where send logger events"),
                }
res_company_amazon_migration()

class amazon_product_category(osv.osv):
    ''' Category for Amazon, also called BrowseNode
    '''
    _name = 'amazon.product.category'
    _description = 'Amazon Category'
    
    _columns = {
        'name':fields.char('Category', size=80, required=True, readonly=False),
        'code':fields.char('Amazon code', size=15, required=True, readonly=False),
        'active': fields.boolean('Active', required=False),
        'parent_id':fields.many2one('amazon.product.category', 'Label', required=False),        
        'destination_id': fields.integer('Destination ID')
    }
    _defaults = {
        'active': lambda *a: True,
        'parent_id': lambda *a: False,
    }
amazon_product_category() 

class product_product_merger(osv.osv):
    ''' Extra fields in product for manage migration on Amazon Database
    '''
    _name = 'product.product'
    _inherit = 'product.product'
    
    # Schedules action:
    def schedule_inventory_etl_import(self, cr, uid, path, file_name, extra_file, context=None):
        ''' Script to import inventory elements in product (for Amazon)
            Inventory value comes from Account program
            After importing are raise event to migrate on Amazon OpenERP DB

            File name is passed in schedule event
            The extra file is a file that have extra_file value char on the name
            this file have inventory to add to original product
            es.: file.csv     extra_file="c"     files.csv.c
        '''
        import logging, os

        def inventory(value):
            '''Clean string for conversion in int
            '''            
            tmp=value.strip() or "0"
            return int(tmp.split(",")[0])            
            
        try:
            comment="Start import CSV inventory files"
            _logger = logging.getLogger('amazon_product_merger')
            _logger.info('Start importing inventory for product!')

            if not path and not file_name:
                _logger.error('Set parameter setted up in scheduler action')
                return 
            
            # Read and store basic file:
            comment="Read basic inventory files: %s"%(file_name)
            csv_file = os.path.join(os.path.expanduser(path), file_name)
            f=open(csv_file, "r")
            f_out=open(csv_file + ".log", "w")            
            i = len_line = 0
            inventory_list = {} # Inventory list (from file) used for add "extra" data
            for csv_line in f:
                i+=1
                line=csv_line.split(";")
                if len_line==0: len_line=len(line)   # first time
                inventory_list[line[0].strip()]=inventory(line[2])
            f.close()    

            # Read extra file and append inventory to stored value    
            tot=i
            if extra_file:
                file_name_extra="%s.%s"%(file_name, extra_file)
                comment="Read extra inventory files: %s"%(file_name_extra)
                csv_file = os.path.join(os.path.expanduser(path), file_name_extra)
                f=open(csv_file, "r")
                i = len_line = 0
                for csv_line in f:
                    i+=1
                    line=csv_line.split(";")
                    if len_line==0: len_line=len(line)   # first time
                    code = line[0].strip()[1:]
                    if code in inventory_list:   # Remove first char
                        inventory_list[code] += inventory(line[2])
                f.close()    

            # Insert fisically the element on DB:            
            comment="Insert CSV file read in DB"
            total=0
            email=""
            for code in inventory_list:
                item_id = self.search(cr, uid, [('default_code','=',code)], context=context) 
                if item_id:                                
                    if not email: # Get parameter: Email for send log:
                        email=self.browse(cr, uid, item_id, context=context)[0].company_id.amazon_log_mail
                    total += 1
                    modify = self.write(cr, uid, item_id[0], {'amazon_mig_inventory': inventory_list[code]}, context=context)             
                    f_out.write("%s;%s\n"%(code,inventory_list[code]))
            total_element="\nTOTAL: %s"%(total)
            f_out.write(total_element)        
            f_out.close()
            
            _logger.info('End importing inventory # of product: %s'%(tot))        
            
            # Launch migration for move in BD Amazon the new values
            self.migrate_product(cr, uid, context=context)

            # TODO launch publication for update web  (vedere altra esportazione per i tempi)
            
            #########################
            # Send log of operation #
            #########################
            log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                                     title="Import company inventory DB: %s [tot.: %s]"%(cr.dbname, total or 0), 
                                     text="Import inventory from company into OpenERP DB.\nThe product are also migrated to Amazon Company DB",
                                     typology='info', 
                                     email=email,         # to recipient
                                     attachment=csv_file, # name of log file
                                     context=context)
        except:
            _logger.error('Error scheduler operation during: %s'%(comment))                    
            try:
                ###############################
                # Send error log of operation #
                ###############################
                comment1 = "Error try to log and mail error!"
                log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                                         title = "Error import company inventory DB: %s"%(cr.dbname,), 
                                         text = "Error import inventory from company into OpenERP DB: %s"%(comment),
                                         typology = 'error', 
                                         email = email,    # to recipient
                                         context = context)
            except:                             
                _logger.error('Error logging error in "log and mail": %s'%(comment1))
        return

    # On Change function:
    """
    def onchange_migrate_test_mandatory_element(self, cr, uid, ids, amazon_mig_migration, amazon_mig_publish, ean13, context=None):
        ''' Test if amazon_mig_migration value is True that some mandatory fields
            are presents, instead of set to false and send a warning
        '''
        res={}
        #if amazon_mig_migration:
        #   if not ean13:
        #      res['value']={}
        #      #res['value']['amazon_mig_migration']=False
        #      res['value']['amazon_mig_publish']=False              
        #      #res['warning']={'title':'Error mandatory fields:', 'message': 'Compile EAN13 value for create Amazon product!'}
        return res"""
    
    # Utility function
    def mapping_data_record(self, cr, uid, product, context=None): # To be overrided!
        ''' Procedure that is overrided with the one in amazon_product_merger_cx
            module for substiture some fields with other values
        '''
        res = {}
        return res
        
    def generate_data_record(self, cr, uid, product, context=None):
        ''' Generate dict for update/create record in Amazon database         
        '''        
        def clean_article(name):
            ''' Remove format "[code] name" return only "name"            
            '''
            temp=name.split("] ")
            if len(temp)==2:
               return temp[1]
            return name   
         
        if product.company_id.amazon_security_inventory: # check parameter on Company
            inventory = product.amazon_mig_inventory - product.amazon_mig_security_level if product.amazon_mig_inventory > product.amazon_mig_security_level else 0
        else:
            inventory = product.amazon_mig_inventory if product.amazon_mig_inventory > 0 else 0
            
        res = {
               'name': product.name,
               'default_code': product.default_code,
               'ean13': product.ean13,

               'amazon_category1_id': product.amazon_mig_category1_id.destination_id if product.amazon_mig_category1_id else False,
               'amazon_category2_id': product.amazon_mig_category2_id.destination_id if product.amazon_mig_category1_id else False,               
               'amazon_warranty': product.amazon_mig_warranty,               
               'amazon_min_level': product.amazon_mig_min_level,
               'amazon_inventory': inventory,
               # product.amazon_mig_security_level not migrated!
               
               #'amazon_force_inventory': product.amazon_mig_force_inventory,    # TODO set to False origin!
               #'amazon_force_availability': product.amazon_mig_force_availability,
               # amazon_inventory"
               'amazon_published': product.amazon_mig_publish,
               'amazon_image_publish': product.amazon_mig_image_publish,
               
               'amazon_title': product.amazon_mig_title or clean_article(product.name),  # update with name if not present title
               'amazon_q_x_pack': product.amazon_mig_q_x_pack,
               'amazon_description': product.amazon_mig_description or clean_article(product.description_sale), # update with sale description if not present
               'amazon_manufacturer': product.amazon_mig_manufacturer,
               'amazon_brand': product.amazon_mig_brand,
               'amazon_sale_start': product.amazon_mig_sale_start,
               'amazon_sale_end': product.amazon_mig_sale_end,
               'amazon_country_id': product.amazon_mig_country_id.id if product.amazon_mig_country_id else False,
               'amazon_is_gift': product.amazon_mig_gift,
               #'amazon_designer'
               #'amazon_is_wrap'
               #'amazon_is_discontinued'
               'amazon_out': product.amazon_mig_out,
               'amazon_function': product.amazon_mig_function,
               'amazon_keywords': product.amazon_mig_keywords,
               'amazon_manage_days': product.amazon_mig_manage_days,
               'amazon_color': product.amazon_mig_color,
               'amazon_material': product.amazon_mig_material,
               
               # Price:
               'amazon_price': product.amazon_mig_price,
               'amazon_discount_price': product.amazon_mig_discount_price,
               'amazon_discount_start': product.amazon_mig_discount_start,
               'amazon_discount_end': product.amazon_mig_discount_end,
               
               # Dimension:
               'amazon_length': product.amazon_mig_length,
               'amazon_width': product.amazon_mig_width,
               'amazon_height': product.amazon_mig_height,
               'amazon_dimension_um': product.amazon_mig_dimension_um,
               # Volume
               'amazon_volume': product.amazon_mig_volume,
               'amazon_volume_um': product.amazon_mig_volume_um,
               # Weight
               'amazon_weight': product.amazon_mig_weight,
               'amazon_weight_um': product.amazon_mig_weight_um,               
                }
        # Update with field used in DB (every DB has his meta fields used!        
        res.update(self.mapping_data_record(cr, uid, product, context=context))
        return res
         
    def migrate_product(self, cr, uid, context=None):
        ''' Migrate all product market for migration on DB used for manage 
            Amazon product
            Callable from xml-rpc in the night schedule or forcable with button 
            from Wizard
        '''
        import xmlrpclib, osv
        
        # Set up parameters (for connection to Open ERP Database) ********************************************
        dbname = "redesiderio" # TODO prelevare dalla configurazione Company
        user = "admin"
        pwd = "cgp.fmsp6"
        server = 'localhost'
        port = '8069'
        if not(dbname and user and pwd): # error
             raise osv.except_osv('Error!', 'Setup database access in Company form!')

        sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
        uid2 = sock.login(dbname, user, pwd)
        if not uid2:
             raise osv.except_osv('Error!', 'Bad login for user %s in destination DB: %s!'%(user, dbname))
            
        sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)        

        # TODO manage: amazon_mig_destination_code
        migration_ids = self.search(cr, uid, [('amazon_mig_migration','=',True)], context=context)
        for product in self.browse(cr, uid, migration_ids, context=context):
            data = self.generate_data_record(cr, uid, product, context=context)
            data.update({'amazon_origin_db': cr.dbname,})
            item_ids = sock.execute(dbname, uid2, pwd, 'product.product', 'search', [('default_code', '=', product.default_code),('amazon_origin_db', '=', cr.dbname),])            

            if item_ids:  # modify
                modify_id = sock.execute(dbname, uid2, pwd, 'product.product', 'write', item_ids, data)            
            else:         # create
                new_id = sock.execute(dbname, uid2, pwd, 'product.product', 'create', data)
                # TODO save record ID??
            self.write(cr, uid, product.id, {#'amazon_mig_force_inventory': False,
                                             'amazon_mig_image_publish': False
                                             }) # return to zero (forced in other DB)
        return 

    # button method
    def migrate_product_button(self, cr, uid, ids, context=None):
        ''' Button event for export all migrate product marked
        '''
        self.migrate_product(cr, uid, context=context)
        return True

    # function fields:
    def _is_amazon_image(self, cr, uid, ids, field_name, arg, context=None):
        ''' Test if exist amazon image file
        '''
        import os
        
        res={}
        for product in self.browse(cr, uid, ids, context=context):
            if product.default_code:
                res[product.id] = os.path.exists("/home/administrator/photo/%s/product/default/%s.jpg"%(cr.dbname, product.default_code.replace(" ", "_")))
            else:   
                res[product.id] = False
        return res

    def _get_amazon_image(self, cr, uid, ids, field_name, arg, context=None):
        ''' Read image from file (according to default folder for every DB 
            that own the linked to image)
        '''
        import base64, urllib, os

        res={}
        if ids:
            for product in self.browse(cr, uid, ids, context=context):
                if product.default_code:
                    file_name = "/home/administrator/photo/%s/product/default/%s.jpg"%(cr.dbname, product.default_code.replace(" ", "_"))
                    try: # Original image:
                        (filename, header) = urllib.urlretrieve(file_name)
                        f = open(filename , 'rb')
                        img = base64.encodestring(f.read())
                        f.close()
                    except:
                        img = False
                else:
                    img = False   
                res[product.id] = img
        return res
        
    _columns = {
               'amazon_mig_category1_id':fields.many2one('amazon.product.category', 'Amazon category 1', required=False, help="Also called Browse Node in Amazon"),
               'amazon_mig_category2_id':fields.many2one('amazon.product.category', 'Amazon category 2', required=False, help="Also called Browse Node in Amazon"),
               'amazon_mig_warranty':fields.boolean('Show warranty', required=False, help="If true, show warranty terms setted in Amazon DB"),

               'amazon_mig_min_level': fields.integer('Re-order level', help="Quantity considered as minumum level of availability, used for highlight product or produce action"),
               'amazon_mig_inventory': fields.integer('Company inventory', help="Product in stock available (inventory from account program, batch imported)"),
               'amazon_mig_security_level': fields.integer('Security level', help="Every real disponibility are decremented for security level so, Amazon has less that real stock products (Amazon=Company-Security)"),

               'amazon_mig_image':   fields.function(_get_amazon_image, type="binary",  string="Preview",   method=True, store=False), #multi="Load image", 
               'amazon_mig_is_image':fields.function(_is_amazon_image, type="boolean", string="Image find", method=True, store=False),

               #'amazon_mig_force_inventory': fields.boolean('Force inventory', required=False, help="Force quantity on inventory"),
               #'amazon_mig_force_availability': fields.integer('Force availability', help="Force availability on Amazon (inventory quantity that override Amazon store"),

               # Manage migration fields:
               'amazon_mig_migration': fields.boolean('Migrate on Amazon company', required=False, help="Migrate on Amazon company, there is set up effetvtively publication on MWS"),
               'amazon_mig_publish': fields.boolean('Published on Amazon company', required=False, help="Published on Amazon"),
               'amazon_mig_image_publish': fields.boolean('Force image publish', required=False, help="Force FTP of image for publishing on Amazon (feed after)"),
               'amazon_mig_destination_code': fields.char('Destination code', size=25, required=False, help="Product code that is create on the Company that publish on Amazon, elsewhere is the default"),
               # Note: depending on original DB, some fields maybe non represented
               # on the view case we use original fields of product (if yet present)
               
               # Amazon anagrafic fields:
               'amazon_mig_title':fields.char('Amazon title', size=100, required=False, readonly=False, help="Leave empty for take name of the product in OpenERP"),  # or name              
               'amazon_mig_q_x_pack': fields.integer('Q. x pack', help="Quantity per pack"),
               'amazon_mig_description':fields.text('Amazon description', required=False, readonly=False, help="Leave empty if you want take sale description instead of this text"),
               #'amazon_mig_designer'
               'amazon_mig_manufacturer':fields.char('Amazon manufacturer', size=64, required=False, readonly=False),                
               'amazon_mig_brand':fields.char('Amazon brand', size=64, required=False, readonly=False),                
               'amazon_mig_sale_start': fields.date('Amazon sale start date'),
               'amazon_mig_sale_end': fields.date('Amazon sale end date'),
               'amazon_mig_country_id':fields.many2one('res.country', 'Amazon origin (country)'),               
               'amazon_mig_gift':fields.boolean('Amazon gift', required=False),
               'amazon_mig_out':fields.boolean('Amazon out of production', required=False),
               'amazon_mig_function':fields.text('Principal function', required=False),
               'amazon_mig_keywords':fields.text('Keywords', required=False),
               'amazon_mig_manage_days': fields.integer('Amazon Manage days', help="Important for manage order, usually 2 days, after are added automatically the days for delvery, not managed, depend on carrier"),
               #amazon_mig_condition (list)
               #amazon_mig_condition_note 

               # Caracteristic:
               'amazon_mig_color':fields.char('Color', size=50, required=False, readonly=False),                               
               'amazon_mig_material':fields.char('Material', size=50, required=False, readonly=False),                               
               
               # Price:
               'amazon_mig_price': fields.float('Amazon price', digits=(16, 2)),
               'amazon_mig_discount_price': fields.float('Amazon discount price', digits=(16, 2)),
               'amazon_mig_discount_start': fields.date('Start discount price'),
               'amazon_mig_discount_end': fields.date('End discount price'),
               # TODO UM price
               
               # Dimension:
               'amazon_mig_length': fields.float('Amazon Length', digits=(16, 2)),
               'amazon_mig_width': fields.float('Amazon Width', digits=(16, 2)),
               'amazon_mig_height': fields.float('Amazon Height', digits=(16, 2)),
               'amazon_mig_dimension_um':fields.char('Dimension UM', size=20, required=False, readonly=False),                
               # Volume
               'amazon_mig_volume': fields.float('Amazon Volume', digits=(16, 2)),
               'amazon_mig_volume_um':fields.char('Volume UM', size=20, required=False, readonly=False),                
               # Weight
               'amazon_mig_weight': fields.float('Amazon Weight', digits=(16, 2)),
               'amazon_mig_weight_um':fields.char('Weight UM', size=20, required=False, readonly=False),                
               }
               
    _defaults = {
                 'amazon_mig_inventory': lambda *a: 0,
                 'amazon_mig_security_level': lambda *a: 5,
                 'amazon_mig_min_level': lambda *a: 3,
                 'amazon_mig_manufacturer': lambda *a: "Re Desiderio",
                 'amazon_mig_brand': lambda *a: "Re Desiderio",
                 'amazon_mig_dimension_um': lambda *a: "Cm",
                 'amazon_mig_volume_um': lambda *a: "M3",
                 'amazon_mig_weight_um': lambda *a: "Kg",
                 'amazon_mig_manage_days': lambda *a: 4,
                 'amazon_mig_q_x_pack': lambda *a: 1,
                 'amazon_mig_warranty': lambda *a: True,
    }          
product_product_merger()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
