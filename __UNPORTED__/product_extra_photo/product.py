# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
import base64
import urllib
from openerp import tools
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

# Parameters for folder and images:
empty_image = "0.png"        
image_extension = "jpg"

root_path = os.path.expanduser("~/photo/")

# Virtuemart image format:
# - Category
category_path = root_path + "%s/category/"
category_resized_path = root_path + "%s/category/resized/"

# - Product
product_path = root_path + "%s/product/default/"
product_resized_path = root_path + "%s/product/resized/"

# - Extra
image_path_par = root_path + "%s/extra/default/"  
resized_path_par = root_path + "%s/extra/resized/"

# K2 Image format:
k2_product_path = root_path + "%s/product/k2/%s/"
image_type = ["Generic", "L", "M", "S", "XL", "XS", "src"]

# vedere se si può eliminare i path di sotto (tenendo la lista di sopra):
k2_product_resized_path_Generic = root_path + "%s/product/k2/Generic/"
k2_product_resized_path_L = root_path + "%s/product/k2/L/"
k2_product_resized_path_M = root_path + "%s/product/k2/M/"
k2_product_resized_path_S = root_path + "%s/product/k2/S/"
k2_product_resized_path_XL = root_path + "%s/product/k2/XL/"
k2_product_resized_path_XS = root_path + "%s/product/k2/XS/"

class res_company_inherit(osv.osv):
    ''' Add extra fields to company
    '''    
    _name = 'res.company'
    _inherit = 'res.company'
    
    _columns = {
        'k2_image_format':fields.boolean('K2 Image format', required=False),
        }
res_company_inherit()

class product_extra_photo_type(osv.osv):
    _name = 'product.extra.photo.type'
    _description = 'Type of photo'
    
    _columns = {
        'name':fields.char('Name', size=64, required=True, readonly=False),
        'char':fields.char('Char', size=4, help="Extra char after code, like: 'code_product.extra_char.ext', must be unique!", required=True, readonly=False),
        'path':fields.char('Path folder', size=128, required=True, readonly=False, help="Default path where photo are stored, use something like: /home/administrator/photo/"),
    }
    
    _sql_constraints = [('char_uniq', 'unique(char)', 'Char reference must be unique!'),]
product_extra_photo_type()

class product_extra_photo(osv.osv):
    _name = 'product.extra.photo'
product_extra_photo()

class product_product_extra_photo(osv.osv):
    """
    Product extra photo
    """    
    _name = 'product.product'
    _inherit = 'product.product'

    image_type=["Generic","L","M","S","XL","XS","src"] # used in other modules for K2 image product
    
    def get_web_image_name(self, cr, uid, item_id, fullpath=True, resize=False, k2_type="src", context=None):
       ''' Get image web name (both K2 and VM, testing DB setup)
       '''
       product_browse=self.browse(cr, uid, item_id, context=context)
       if product_browse:
           if product_browse.k2_image_format: # K2 format
               f_n="%s.%s"%(product_browse.default_code,image_extension)
               if fullpath:
                  # TODO (manage K2 resize image foto (list?)
                  #if resize:
                  #return "%s%s.%s"%(product_resized_path%(cr.dbname),product_browse.default_code,image_extension)
                  #else:       "/media/k2/items/src/"
                  return "%s%s"%(k2_product_path%(cr.dbname, k2_type), f_n)
               else:   
                  return f_n
           else: # Virtuemart format:           
               if fullpath:
                  if resize:
                     return "%s%s.%s"%(product_resized_path%(cr.dbname),product_browse.default_code,image_extension)
                  else:
                     return "%s%s.%s"%(product_path%(cr.dbname),product_browse.default_code,image_extension)
               else:   
                  return "%s.%s"%(product_browse.default_code,image_extension)
       else:
           return ""   

    def get_empty_web_image_name(self, cr, uid, item_id, context=None):
       ''' Get image web name empty (not finded, only for show in OpenERP)
       '''
       # TODO for K2?
       return "%s%s"%(product_path%(cr.dbname),empty_image)
    
    def get_web_image(self, cr, uid, item_id, context=None):
        ''' Read image from file (default folder)
        '''        
        img = ''
        if item_id:
            try: # immagine originale
                (filename, header) = urllib.urlretrieve(self.get_web_image_name(cr, uid, item_id, context=context))
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            # immagine vuota:
            if not img:       
                try:
                    (filename, header) = urllib.urlretrieve(self.get_empty_web_image_name(cr, uid, item_id, context=context))
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''                
        return img
    
    def _get_web_image(self, cr, uid, ids, field_name, arg, context=None):
        ''' Return image from file for every product
        '''
        # Create folder path if not exist:
        import os

        #TODO for K2?
        try: # product                      # TODO Mettere nella init del modulo
           os.makedirs(product_resized_path%(cr.dbname)) # create product and product resized path
        except:
           pass # no error   
        try: # product                      # TODO Mettere nella init del modulo
           os.makedirs(product_path%(cr.dbname)) # create product and product resized path
        except:
           pass # no error   
        try: # category
           os.makedirs(category_resized_path%(cr.dbname)) # create category and category resized path
        except:
           pass # no error   
        
        res = {}
        for item in ids:
            res[item] = self.get_web_image(cr, uid, item, context=context)
        return res                
        
    _columns = {
        # Product photo for web (code.jpg):
        # TODO scan folder procedure
        'web_image_preview':fields.function(_get_web_image, type="binary", method=True),
        'web_image_create_time':fields.char('Create time ID', size=64, required=False, readonly=False, help="Only default image is saved for test timestamp, so: resized publishing depend on default image"),
        'web_image_update':fields.boolean('To update', required=False, help="When import images, this field highlight if image is modified (used for operation like publish on web for only new/modify importation)",),
        
        # Product extra photo for web:
        'extra_photo_ids':fields.one2many('product.extra.photo', 'product_id', 'Extra photo', required=False),
        'k2_image_format': fields.related('company_id','k2_image_format', type='boolean', string='K2 Image format'),
    }
    _defaults = {
        'web_image_update': lambda *a: False, # Procedure decide to update!
    }
product_product_extra_photo()

class product_extra_photo_inherit(osv.osv):
    _name = 'product.extra.photo'
    _inherit = 'product.extra.photo'
    _description = 'Extra photo'

    # Utility function:
    def get_image_name(self, cr, uid, item_id, complete=False, context=None):
        ''' get ID of extra image
            return complete name of image 
            if complete=True with full path
               compelte=False only name
        '''
        product_photo_browse=self.browse(cr, uid, item_id)
        image_path = image_path_par%(cr.dbname)
        if complete:  
            return "%s%s.%s.%s.%s"%(image_path, product_photo_browse.product_id.code, product_photo_browse.type_id.char, product_photo_browse.name, image_extension) 
        else:
            return "%s.%s.%s.%s"%(product_photo_browse.product_id.code, product_photo_browse.type_id.char, product_photo_browse.name, image_extension)
    
    def import_images(self, cr, uid, item_id, context=None):
        ''' Procedure that read all image folder and import in extra photo of
            product all images finded, for all resolution setted up and saving
            information about time stamp (testing if image is modified)
            
            In this prodedur default product photo attribute are checked for 
            check publish box if need web update
            fore K2 (only default photo) and VM
        '''
        import os
        from os.path import join, getsize, getctime, getmtime, getatime
        import logging
        _logger = logging.getLogger('gpb_web')

        _logger.info('Begin syncro images:')

        # Load pool used in import procedure:
        product_pool=self.pool.get('product.product')
        image_extra_pool=self.pool.get('product.extra.photo')
        image_type_pool=self.pool.get('product.extra.photo.type')
        
        parameter_pool=self.pool.get('web.shop.parameter')
        parameter_ids = parameter_pool.search(cr, uid, [('company_id','=',1)], context=context)  # TODO parametrize
        if not parameter_ids:
           return False
        parameters = parameter_pool.browse(cr, uid, parameter_ids, context=context)[0] 
        is_k2 = parameters.company_id.k2_image_format

        # parameter for K2 test ******************************************************************************************************
        if not is_k2:
            # set up flag "delete" for all images (only new and update will change it):
            all_extra_images = self.search(cr, uid, [])
            set_for_deletion = self.write(cr, uid, all_extra_images, {'delete': True,})

        # TODO loop on all categories
        #for category in image_type_pool.browse(cr,uid,image_type_pool.search(cr, uid, [])): # all category
        #    image_path=category.path or "/home/administrator/photo/"
        
        # set up parameters:                
        if is_k2: # K2 path
            # NOTE: not created here the path!
            product_image_path = k2_product_path%(cr.dbname, "src")   # for product
            pass
        else:     # VM path
            product_image_path = product_path%(cr.dbname)   # for product
            image_path = image_path_par%(cr.dbname)         # for extra product
            resized_path = resized_path_par%(cr.dbname)     # not used (for extra product)                
            try: # Create root folder
               os.makedirs(root_path)
            except:
               pass # raise no error
            try: # Create product folder
               os.makedirs(product_image_path)
            except:
               pass # raise no error
            try: # Create product extra folder
               os.makedirs(image_path)
            except:
               pass # raise no error
            try: # Create resized product extra folder (TODO unused for now)
               os.makedirs(resized_path)
            except:
               pass # raise no error

            if not os.path.exists(product_image_path):
               raise osv.except_osv('Error searching database folder path (extra images): %s'%(image_path))
               
            if not os.path.exists(image_path):
               raise osv.except_osv('Error searching database folder path (extra images): %s'%(image_path))

        # SYNCRO PRODUCT IMAGE *************************************************
        _logger.info('- Product images:')
        # Create a list for test after when readin images:
        time_stamp={}
        product_ids=product_pool.search(cr, uid, [], context=context)  # all products!
        for product in product_pool.browse(cr, uid, product_ids, context=context):
            time_stamp[product.default_code]=(product.id, product.web_image_create_time)   # (id, getmtime)

        for root, dirs, files in os.walk(product_image_path):
            for f in files:                            
                file_name=f.lower().split(".")
                if len(file_name)==2 and file_name[1]==image_extension:  # (code, extension)
                   # Search product_id from code:
                   if file_name[0] in time_stamp:
                      ts = "%0.2f"%getmtime(join(root, f))
                      if ts != time_stamp[file_name[0]][1]: # NOTE TS is saved as float 2 dec.!
                         product_pool.write(cr, uid, time_stamp[file_name[0]][0], {'web_image_create_time': ts,'web_image_update':True}, context=context)

        if not is_k2:
            # SYNCRO PRODUCT EXTRA IMAGE *************************************************
            _logger.info('- Product extra images:')
            for root, dirs, files in os.walk(image_path):
                for f in files:
                    file_name=f.lower().split(".")
                    if (len(file_name)==4) and (file_name[3]==image_extension):  # (code, char type, num, extension)
                       # Search product_id from code:
                       product_ids=product_pool.search(cr, uid, [('default_code', '=', file_name[0])]) 
                       # Search type of extra image from letter
                       type_ids=image_type_pool.search(cr, uid, [('char', '=', file_name[1])]) # TODO use ilike?
                       
                       if product_ids and type_ids: # TODO only one element or more? TODO print error?
                          mtime="%0.2f"%(getmtime(join(root, f)))
                          # Test if exist (with same time code, instead of search and read element, I use 2 search):
                          image_extra_ids = image_extra_pool.search(cr, uid, [('product_id', '=', product_ids[0]),
                                                                              ('name', '=', file_name[2]),
                                                                              ('type_id', '=',type_ids[0]),
                                                                              ('create_time', '=', mtime)]) # is modify!
                          if image_extra_ids: # update only delete field
                             image_extra_pool.write(cr, uid, image_extra_ids[0], {'delete': False,})
                          else: # Test if exist (without time code):
                             image_extra_ids = image_extra_pool.search(cr, uid, [('product_id', '=', product_ids[0]),
                                                                                 ('name','=', file_name[2]),
                                                                                 ('type_id','=', type_ids[0]),])
                             if image_extra_ids: # update (with publish flag)
                                image_extra_pool.write(cr, uid, image_extra_ids[0], {'delete': False,
                                                                                     'create_time': mtime,
                                                                                     'update': True, # was modified
                                                                                     'size': 0,
                                                                                    })
                             else: # new element
                                image_extra_pool.create(cr, uid, {'delete': False,
                                                                  'name': file_name[2],
                                                                  'type_id': type_ids[0],
                                                                  'product_id': product_ids[0],
                                                                  'create_time': mtime,
                                                                  'dimension': '200', # TODO parametrize?
                                                                  'update': True,
                                                                  'size': 0,
                                                                  })
                break # TODO import other "dimension folder"
            # delete images that doesn't have modified flag delete:
            all_extra_images = self.search(cr, uid, [('delete','=',True)])
            set_for_deletion = self.unlink(cr, uid, all_extra_images)
            
        _logger.info('End sycro images')
        return True
        
    def get_image(self, cr, uid, item_id, context=None):
        ''' Get folder (actually default folder) and extension from folder obj.
            Calculated dinamically image from module image folder + extra path + ext.
            Return image
        '''
        import os
        img = ''        
        product_photo_browse=self.browse(cr, uid, item_id)

        # TODO Parametrize this elements:
        image_path = image_path_par%(cr.dbname)
        if product_photo_browse.product_id.code:
            try: # Immagine composta col nome codice:
                (filename, header) = urllib.urlretrieve(self.get_image_name(cr, uid, item_id, complete=True, context=context)) 
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            
            if not img:   # immagine vuota:
                try:
                    (filename, header) = urllib.urlretrieve(image_path + empty_image)
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''                
        return img
    
    def _get_image(self, cr, uid, ids, field_name, arg, context = None):
        if context is None:
           context = {}
           
        res = {}
        for item in ids:
            res[item] = self.get_image(cr, uid, item)
        return res  
            
    _columns = {
        'name':fields.char('Name', size=64, required=False, readonly=False),
        'preview':fields.function(_get_image, type="binary", method=True),
        'type_id':fields.many2one('product.extra.photo.type', 'Type of photo', required=False),
        'product_id':fields.many2one('product.product', 'Product', required=False),
        'create_time':fields.char('Create time ID', size=64, required=False, readonly=False),
        'dimension':fields.char('Dimension', size=64, help="Usually width of image, used also for folder name that contains this particular image", required=False, readonly=False),
        'update':fields.boolean('To update', required=False, help="When import images, this field highlight if image is modified (used for operation like publish on web for only new/modify importation)",),
        'delete':fields.boolean('To delete', required=False, help="When import all images are set up for delete, only update and new are correct this value",),
        'size': fields.integer_big('Size image'),
    }
    
    _defaults = {
        'dimension': lambda *x: "200",
        'delete': lambda *x: False,
    }
product_extra_photo_inherit()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
