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
from datetime import datetime

k2_parameters="catItemTitle=\ncatItemTitleLinked=\ncatItemFeaturedNotice=\ncatItemAuthor=\ncatItemDateCreated=\ncatItemRating=\ncatItemImage=\ncatItemIntroText=\ncatItemExtraFields=\ncatItemHits=\ncatItemCategory=\ncatItemTags=\ncatItemAttachments=\ncatItemAttachmentsCounter=\ncatItemVideo=\ncatItemVideoWidth=\ncatItemVideoHeight=\ncatItemVideoAutoPlay=\ncatItemImageGallery=\ncatItemDateModified=\ncatItemReadMore=\ncatItemCommentsAnchor=\ncatItemK2Plugins=\nitemDateCreated=\nitemTitle=\nitemFeaturedNotice=\nitemAuthor=\nitemFontResizer=\nitemPrintButton=\nitemEmailButton=\nitemSocialButton=\nitemVideoAnchor=\nitemImageGalleryAnchor=\nitemCommentsAnchor=\nitemRating=\nitemImage=\nitemImgSize=\nitemImageMainCaption=\nitemImageMainCredits=\nitemIntroText=\nitemFullText=\nitemExtraFields=1\nitemDateModified=\nitemHits=\nitemTwitterLink=\nitemCategory=\nitemTags=\nitemShareLinks=\nitemAttachments=\nitemAttachmentsCounter=\nitemRelated=\nitemRelatedLimit=\nitemVideo=\nitemVideoWidth=\nitemVideoHeight=\nitemVideoAutoPlay=\nitemVideoCaption=\nitemVideoCredits=\nitemImageGallery=\nitemNavigation=\nitemComments=\nitemAuthorBlock=\nitemAuthorImage=\nitemAuthorDescription=\nitemAuthorURL=\nitemAuthorEmail=\nitemAuthorLatest=\nitemAuthorLatestLimit=\nitemK2Plugins="

class web_shop_parameter(osv.osv):
    ''' Parameter to access to shop on Joomla! Web Site
    '''    
    _name = 'web.shop.parameter'
    _description = 'Shop Parameter'
    _order="name"

    # Scheduled function:
    def schedule_rename_cript_image_files(self, cr, uid, origin_path, destination_path,context = None):
        ''' Scheduled action for rename files in cript folder
        '''
        import os, tools, xmlrpclib, sys, shutil

        product_pool=self.pool.get('product.product') 
        sock = xmlrpclib.ServerProxy("http://www.gpb.it/www2/xmlrpc/server.php")
        
        image_ids = product_pool.search(cr, uid, [('web','=',True)], context=context) # all web product
        i=0
        for product in product_pool.browse(cr, uid, image_ids, context=context):
            i+=1
            try:
                hash_name = sock.openerp.getSecureHRMD5(product.default_code) 
                if hash_name:
                    origin= os.path.expanduser("%s%s.jpg"%(origin_path, product.default_code))
                    destination= os.path.expanduser("%s%s.jpg"%(destination_path, hash_name))
                    
                    shutil.copy2(origin, destination)
                    #f.write("cp %s %s\n"%(origin, destination))
                    print "Renamed, code: %s > %s"%(product.default_code, hash_name)
                else:    
                    print "Hash null, code: %s"%(product.default_code)
            except:
                print "Error renaming product %s"%(product.default_code)
        return True 
    
    #TODO Creare il file PHP
    """ 
    <?php
    $username="admin";
    $password="password";
    $database="database";
    $prefix="jgpb_";

    $log_file="../micronaet.log"; // Root del sito!
    ?>
    """
    _columns = {
        'name':fields.char('Shop', size=80, required=True, readonly=False, help="Shop name linked to web site, ex. http://www.example.it/shop/"),
        'company_id':fields.many2one('res.company', 'Company', required=True, help="Company linked to this web shop"),
        #'k2':fields.boolean('Joomla 1.5 with K2', required=False), # TODO tolto, spostato in company
        'k2_image_format': fields.related('company_id','k2_image_format', type='boolean',string='K2 site format'),
        'web_site':fields.char('Web site', size=120, required=True, readonly=False, help=r"Web site address, like: http://www.example.it (used for link to XML-RCP service that need to installed before on Joomla! web)"),
        'logfile_name':fields.char('Log file', size=120, required=True, readonly=False, help=r"Web log file where application save all importazion events, defaul = 'micronaet.log'"),

        # MySQL parameter:
        'mysql_username':fields.char('Username', size=80, required=True, readonly=False, help="MySql: Username"),
        'mysql_password':fields.char('Password', size=80, required=True, readonly=False, help="MySql: Password"),
        'mysql_prefix_table':fields.char('Table prefix', size=10, required=True, readonly=False, help="MySql: Table prefix, used in Joomla! ex. 'jos_'"),
        'mysql_database':fields.char('Database', size=80, required=True, readonly=False, help="Database name"),

        # FTP parameter:
        'ftp_server':fields.char('Server', size=80, required=False, readonly=False, help="FTP: Server name, ex. www.example.it"),
        'ftp_username':fields.char('Username', size=80, required=False, readonly=False, help="FTP: Username"),
        'ftp_password':fields.char('Password', size=80, required=False, readonly=False, help="FTP: Password"),
        'ftp_home':fields.char('Home directory', size=100, required=False, readonly=False, help="FTP: Home directory, like /home/administrator"),
        
        # FTP parameter:
        'joomla_username':fields.char('Username', size=80, required=False, readonly=False, help="Joomla!: Username"),
        'joomla_password':fields.char('Password', size=80, required=False, readonly=False, help="Joomla!: Password"),        
        }
    _defaults = {
        'logfile_name': lambda *a: "micronaet.log",
        #'k2': lambda *a: False,
    }        
web_shop_parameter()

class web_category(osv.osv):
    ''' Every product have an associated category 
    '''    
    _name = 'web.category'
    _description = 'Web Category'
    _order="sequence,name"
    
    # public utility function (used also in line and color)    
    def get_name(self, cr, uid, item_id, tipology="category", context=None):
        return "%s/category(/resized)/%s_%s.jpg"%(cr.dbname, tipology, item_id)
        
    # fields function:
    def _get_file_name(self, cr, uid, ids, field, params, context=None):
        ''' Return for every field the name of image (and a part of path)
        '''
        res={}
        for item_id in ids: 
            res[item_id]=self.get_name(cr, uid, item_id, context=context)
        return res
        
    _columns = {
        'name':fields.char('Category', size=80, required=True, readonly=False, translate=True),
        'sequence': fields.integer('seq'),
        'file_name': fields.function(_get_file_name, method=True, type="char", size=80, string="Image File name", store=False,),
        }
web_category()

class web_line(osv.osv):
    ''' Every product have an associated line
    '''    
    _name = 'web.line'
    _description = 'Web Line'
    _order="sequence,name"
    
    # fields function:
    def _get_file_name(self, cr, uid, ids, field, params, context=None):
        ''' Return for every field the name of image (and a part of path)
        '''
        res={}
        for item_id in ids: 
            res[item_id]=self.pool.get('web.category').get_name(cr, uid, item_id, tipology="line", context=context)
        return res
        
    _columns = {
        'name':fields.char('Line', size=80, required=True, readonly=False, translate=True),
        'category_id':fields.many2one('web.category', 'Category', required=True),
        'sequence': fields.integer('seq'),
        'file_name': fields.function(_get_file_name, method=True, type="char", size=80, string="Image File name", store=False,),
    }
web_line()

class web_color(osv.osv):
    ''' Every product have an associated line that has a color spec.
    '''    
    _name = 'web.color'
    _description = 'Web color'
    _order="sequence,name"
    
    # fields function:
    def _get_file_name(self, cr, uid, ids, field, params, context=None):
        ''' Return for every field the name of image (and a part of path)
        '''
        res={}
        for item_id in ids: 
            res[item_id]=self.pool.get('web.category').get_name(cr, uid, item_id, tipology="color", context=context)
        return res

    _columns = {
        'name':fields.char('Color', size=80, required=True, readonly=False, translate=True),
        'line_id':fields.many2one('web.line', 'Line', required=True),
        'sequence': fields.integer('seq'),    
        'file_name': fields.function(_get_file_name, method=True, type="char", size=80, string="Image File name", store=False,),
    }
web_color()

class web_line(osv.osv):
    ''' extra relation fields
    '''    
    _name = 'web.line'
    _inherit = 'web.line'
    
    _columns = {
        'color_ids':fields.one2many('web.color', 'line_id', 'Color'),
    }
web_line()

class web_k2_line(osv.osv):
    ''' Every product have an associated line
    '''    
    _name = 'web.k2.line'
    _description = 'Web K2 line'
    _rec_name = "category_id"
    
    _columns = {
        'category_id':fields.many2one('web.category', 'Category', required=True),
        'product_id':fields.many2one('product.product', 'Product', required=True),
    }
web_k2_line()

class web_category(osv.osv):
    ''' extra relation fields
    '''    
    _name = 'web.category'
    _inherit = 'web.category'
    
    _columns = {
        'line_ids':fields.one2many('web.line', 'category_id', 'Line'),
    }
web_category()

class web_tipology(osv.osv):
    ''' Every product have an associated tipology
    '''    
    _name = 'web.tipology'
    _description = 'Web tipology'
    _order="sequence,name"

    _columns = {
        'name':fields.char('tipology', size=80, required=True, readonly=False, translate=True),
        'sequence': fields.integer('seq'),    
        'k2_id':fields.char('ID K2', size=4, required=False, readonly=False),
    }
web_tipology()

class web_custom_filter(osv.osv):
    ''' Custom filter categories
    '''    
    _name = 'web.custom.filter'
    _description = 'Web custom filter'
    _order="sequence,name"
    
    _columns = {
        'name':fields.char('Custom filter', size=80, required=True, readonly=False, translate=True),
        'sequence': fields.integer('seq'),    
        'field_type':fields.selection([
            (1,'Select'),
            (2,'Radio button'),
            (3,'Checkbox'),
            (4,'Link'),
        ],'Field type', required=True, readonly=False),
    }
web_custom_filter()

class web_subtipology(osv.osv):
    ''' Every product have an associated subtipology
    '''
    
    _name = 'web.subtipology'
    _description = 'Web subtipology'

    _columns = {
        'name': fields.char('Subtipology', size=80, required=True, readonly=False, translate=True),
        'tipology_id': fields.many2one('web.tipology', 'Tipology', required=True),
        'custom_filter_id': fields.many2one('web.custom.filter', 'Custom filter', required=False), # TODO True
    }
web_subtipology()

class web_k2_subtipology(osv.osv):
    ''' K2 subtipology name for associate parameter value to product    
    '''
    
    _name = 'web.k2.subtipology'
    _description = 'Web K2 subtipology'

    _columns = {
        'name': fields.char('Value', size=80, required=True, readonly=False, translate=True),
        'tipology_id': fields.many2one('web.tipology', 'Tipology', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=False), 
    }
web_k2_subtipology()

class web_k2_vetrina(osv.osv):
    ''' K2 home vetrina
    '''
    
    _name = 'web.k2.vetrina'
    _description = 'Web K2 Vetrina'

    _columns = {
        'name': fields.char('Vetrina name', size=80, required=True, readonly=False),
        'k2_id': fields.integer('K2 ID on site', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=False), 
        'badge':fields.selection([
            ('new','New prodoct'),
            ('hot','Hot product'),            
        ],'Badge', select=True, readonly=False, required=True),
    }    
    _defaults = {
        'badge': lambda *a: 'new',
    }
web_k2_vetrina()

class web_k2_mod_custom(osv.osv):
    ''' K2 Left custom product module
    '''
    
    _name = 'web.k2.mod.custom'
    _description = 'Web K2 Mod custom'

    _columns = {
        'name': fields.char('Title', size=80, required=True, readonly=False),
        'k2_id': fields.integer('K2 ID on site', help="Automatically generation when import on site", readonly=True),
        'text': fields.text('Text of article'),
        'has_title':fields.boolean('Has title', required=False),
    }    
    _defaults = {
        'text': lambda *a: "<p class='box-grey'>\ndescrizione1<b>valore1</b><br>\ndescrizione2<b>valore2</b><br>\n<br><br></p>",
        'has_title': False,
    }
web_k2_mod_custom()

class web_k2_gallery(osv.osv):
    ''' K2 Images gallery
    '''
    
    _name = 'web.k2.gallery'
    _description = 'Web K2 Gallery'

    def _get_folder_name_function(self, cr, uid, ids, field_name, arg, context=None):
        ''' Generate name of the folder for each element passed (according to 
            DB name and ID
        '''
        res={}
        for item in self.browse(cr, uid, ids, context=context): 
            res[item.id]="photo/%s/product/gallery/%s"%(cr.dbname, item.name)
        return res

    _columns = {
        'name': fields.char('Unique name', size=80, required=True, readonly=False, help="This is also the name of the folder"),
        'long_title': fields.char('Title of gallery', size=80, required=True, readonly=False),
        'k2_id': fields.integer('K2 ID on site', help="Automatically generation when import on site", readonly=True),
        'folder': fields.function(_get_folder_name_function, method=True, type='char', string='Folder root path', store=False),
        'publish':fields.boolean('To publish', required=False),
    }    
web_k2_gallery()

class web_tipology(osv.osv):
    ''' Extra relation fields for tipology
    '''    
    _name = 'web.tipology'
    _inherit = 'web.tipology'

    _columns = {
        'subtipology_ids':fields.one2many('web.subtipology', 'tipology_id', 'Subtipology', required=False),
    }
web_tipology()

class product_product_linked_rel(osv.osv):
    ''' Relation product m2m product
        Every product can have a list of linked child (for "also recomended")
    '''
    _name = "product.product.linked.rel"
    _description = "Product linked relation"
    _rec_name='parent_id'
    _order = 'sequence'
    
    _columns = {
                'parent_id': fields.many2one('product.product', 'Parent', required=True),
                'child_id': fields.many2one('product.product', 'Child', required=True),
                'sequence': fields.integer('seq'),    
                }                
product_product_linked_rel()    

# INHERIT: 
class product_product_web_fields(osv.osv):
    _name='product.product'
    _inherit ='product.product'

    
    def on_change_category(self, cr, uid, ids, category_id, line_id, context=None):    
        if category_id:
            if line_id:
               web_line=self.pool.get('web.line').browse(cr, uid, line_id)
               if category_id != web_line.category_id.id:
                  line_id=False
            else:
               line_id=False
            return {
                   'value' : {'line_id' : line_id,},
                   'domain' : {'line_id': [('category_id','=',category_id)], },
                   }
        else:           
            return {
                   'value' : {'line_id' : False,
                              'color_id': False,
                             },
                   'domain' : {},
                   }

    def on_change_line(self, cr, uid, ids, line_id, color_id, context=None):    
        if line_id:
            if color_id:
               web_color=self.pool.get('web.color').browse(cr, uid, color_id)
               if line_id != web_color.line_id.id:
                  color_id=False
            else:
               color_id=False
            return {
                   'value' : {'color_id' : color_id,},
                   'domain' : {'color_id': [('line_id','=',line_id)], },
                   }
        else:           
            return {
                   'value' : {'color_id' : False,},
                   'domain' : {},
                   }

    def on_change_tipology(self, cr, uid, ids, tipology_id, subtipology_ids, context=None):    
        if tipology_id:
            return {
                'value' : {'subtipology_ids' : [],}, # unlink 
                'domain' : {'subtipology_ids': [('tipology_id','=',tipology_id)], },
               }
        else:           
            return {
                'value' : {'subtipology_ids' : [],},
                'domain' : {},
                }

    _columns = {
            'web': fields.boolean('On Web', required=False),
            #'favourite': fields.boolean('Favourite', required=False, help="Product in evidence, home page or have particulary image effects"),
            'category_id':fields.many2one('web.category', 'Category', required=False),
            'line_id':fields.many2one('web.line', 'Line', required=False),
            'color_id':fields.many2one('web.color', 'Color', required=False),
            'tipology_id':fields.many2one('web.tipology', 'Tipology', required=False, domain="[('parent_id','=',False)]"),
            'subtipology_ids': fields.many2many('web.subtipology','product_subtipology_rel','product_id','subtipoloy_id','Subtipology'),
            
            # Linked product:
            'parent_ids':fields.one2many('product.product.linked.rel', 'parent_id', 'Parent', required=False, help="List of product that have this product as a parent"),
            'child_ids':fields.one2many('product.product.linked.rel', 'child_id', 'Child', required=False, help="List of product that have this product as a child"),
            
            # Description:
            'vm_name': fields.text('VM Name', translate=True),
            'vm_short': fields.text('VM short name', translate=True, help="VM=short text, in K2=introtext formatted"),
            'vm_description': fields.text('VM Description', translate=True, help="VM=description text, in K2=full text formatted"),
            
            # K2 Fields:
            # Title = code 
            # Alias = SKU
            # Ordering = sequence
            'k2_params': fields.text('K2 params', help="In K2 represent some parameters to setup for item form "),
            'k2_gallery': fields.text('K2 gallery', help="In K2 represent formattation of gallery to reproduce"),
            'k2_extra_fields': fields.text('K2 extra fields', help="In K2 represent formatted extra fields value"),
            'k2_extra_field_search': fields.text('K2 gallery', translate=True, help="In K2 represent extra value for search component"),
            'k2_image_caption': fields.text('K2 image caption', translate=True, help="In K2 represent the description of the image"),            
            'k2_introtext': fields.text('K2 intro text', translate=True, help="In K2 represent the description of the image"),            
            'k2_fulltext': fields.text('K2 full text', translate=True, help="In K2 represent the description of the image"),            
            'k2_ordering': fields.integer('Order'),
            'k2_alias':fields.char('alias', size=64, required=False, readonly=False), # TODO temporaneo da togliere dopo
            
            'k2_subtipology_ids':fields.one2many('web.k2.subtipology', 'product_id', 'K2 Extra fields', required=False),
            'k2_category_ids':fields.one2many('web.k2.line', 'product_id', 'K2 Category', required=False),
            'k2_all_product': fields.boolean('K2 All product', required=False, help="See in all product research, else only in accessory"),     # 1 or 3 catid
            'k2_mod_custom_ids':fields.many2many('web.k2.mod.custom', 'product_custom_mod_rel', 'product_id', 'custom_id', 'Custom mod.'),
            'k2_gallery_id':fields.many2one('web.k2.gallery', 'Gallery', required=False),
    }    
product_product_web_fields()

# WIZARD:
class web_wizard(osv.osv_memory):   
    _name='web.wizard'
    _description='Web wizard publish'

    # Utility function:
    def get_k2_extra_fields(self, cr, uid, product):
        ''' Function that create extra syntax fields from o2m relation
            product passed is browse obj of product actually selected
        '''
        #[{"id":"7","value":"49,5x81x49"},{"id":"8","value":"50x82x29,5"},{"id":"9","value":"82x215hx120"},{"id":"10","value":"32"},{"id":"11","value":"64"}]
        res=""
        for st in product.k2_subtipology_ids:                    
            if not res:
               res_append='[{"id":"%s","value":"%s"}'
            else:   
               res_append=',{"id":"%s","value":"%s"}'
            res+= res_append%(st.tipology_id.k2_id,st.name)
        if res:
           res+="]"    
        return res
        
    def ftp_k2_gallery(self, cr, uid, ids, folder_name, context = None):
        ''' Forced publish of K2 image gallery
        '''
        import ftplib, os
        from ftplib import FTP
        import logging

        #wiz_browse=self.browse(cr, uid, ids)[0]
        parameter_pool=self.pool.get('web.shop.parameter')
        parameter_ids = parameter_pool.search(cr, uid, [('company_id','=',1)], context=context)  # TODO parametrize
        if not parameter_ids:
           return False

        parameters = parameter_pool.browse(cr, uid, parameter_ids, context=context)[0] 
        
        destination_path = parameters.ftp_home + "/images/stories/GALLERY/%s/"%(folder_name)
        destination_resized_path = parameters.ftp_home + "/images/stories/GALLERY/%s/thumbs/"%(folder_name)

        ftp = FTP(parameters.ftp_server)
        ftp.login(parameters.ftp_username, parameters.ftp_password)

        folder=os.path.expanduser("~/photo/%s/product/gallery/%s/"%(cr.dbname, folder_name))
        try: 
           ftp.mkd(destination_path)
        except:
           pass   
        ftp.cwd(destination_path)

        for subdir, dirs, files in os.walk(os.path.expanduser(folder)):
            for file in files: 
                image= os.path.join(folder + file)
                image_dest = destination_path + file
                f = open(image, "rb")
                ftp.storbinary('STOR ' + image_dest, f)
                f.close()
            break # only first level    

        folder=os.path.expanduser("~/photo/%s/product/gallery/%s/thumbs/"%(cr.dbname, folder_name))
        try: 
            ftp.mkd(destination_resized_path)
        except:
           pass   
        ftp.cwd(destination_resized_path)        
        for subdir, dirs, files in os.walk(os.path.expanduser(folder)):
            for file in files: 
                image= os.path.join(folder + file)
                image_dest = destination_resized_path + "thumb_" + file
                f = open(image, "rb")
                ftp.storbinary('STOR ' + image_dest, f)
                f.close()
            break # only first level    
        ftp.close()
        return True 

    def ftp_category_products(self, cr, uid, ids, context = None):
        ''' Only for VM: upload category and line photo on web
        '''
        import ftplib
        from ftplib import FTP
        import logging
        import os
        
        _logger = logging.getLogger('gpb_web')
        log_error="Image not found:"

        _logger.info('Start upload category and line images')
        
        wiz_browse=self.browse(cr, uid, ids)[0]
        category_pool=self.pool.get('web.category')
        line_pool=self.pool.get('web.line')
        color_pool=self.pool.get('web.color')
        
        parameter_pool=self.pool.get('web.shop.parameter')
        parameter_ids = parameter_pool.search(cr, uid, [('company_id','=',1)], context=context)  # TODO parametrize
        if not parameter_ids:
           return False

        parameters = parameter_pool.browse(cr, uid, parameter_ids, context=context)[0] 
        ftp = FTP(parameters.ftp_server)
        ftp.login(parameters.ftp_username, parameters.ftp_password)
        
        destination_path = parameters.ftp_home + "/images/stories/virtuemart/category/"
        destination_resized_path = parameters.ftp_home + "/images/stories/virtuemart/category/resized/"
            
        if wiz_browse.force_image: # works only for forced image:
            for pool, comment in ((category_pool, "category"), (line_pool, "line")(color_pool, "color"), ):
                _logger.info('Start upload %s images'%(comment,))
                image_ids = pool.search(cr, uid, [], context=context) # all category or line product
                i=0
                for element in pool.browse(cr, uid, image_ids, context=context):
                    i+=1
                    if i % 50 == 0:
                       _logger.info('... continuing upload %s images, tot: %s'%(comment, i))

                    try:
                        image_name = "%s_%s.jpg"%(comment, element.id)
                        normal_image_name = os.path.expanduser("~/photo/%s/category/%s"%(cr.dbname, image_name))  # TODO vedere di parametrizzare in qualche modo
                        resized_image_name = os.path.expanduser("~/photo/%s/category/resized/%s"%(cr.dbname, image_name))  # TODO vedere di parametrizzare in qualche modo
                        for (image, folder) in ((normal_image_name, destination_path), (resized_image_name, destination_resized_path)):  # Resize and normal FTP
                            image_name_dest = "%s_%s_120x120.jpg"%(comment, element.id) if comment=="line" and folder == destination_resized_path else "%s_%s.jpg"%(comment, element.id) # TODO (per color?????)
                            f = open(image, "rb")
                            ftp.cwd(folder)
                            ftp.storbinary('STOR ' + image_name_dest, f)
                            f.close()
                        # Remove check update in record image (only if 2 image are published!)
                        #product_pool.write(cr, uid, product.id, {'web_image_update':False,}, context=context)                     
                    except:
                        log_error+="%s;"%(image_name)
                        pass # no error, file still unpublished  TODO image not found!!!

        ftp.quit()        
        return log_error

    def ftp_products(self, cr, uid, ids, is_k2, hash_function = None, context = None):
        ''' Pass all unpublished elements in product and put on the web (image files)
        '''
        import ftplib
        from ftplib import FTP
        import logging
        _logger = logging.getLogger('gpb_web')

        wiz_browse=self.browse(cr, uid, ids)[0]
        product_pool=self.pool.get('product.product')
        parameter_pool=self.pool.get('web.shop.parameter')
        log_error="Image not found:"

        parameter_ids = parameter_pool.search(cr, uid, [('company_id','=',1)], context=context)  # TODO parametrize
        if not parameter_ids:
           return False

        if not is_k2 and not hash_function: # ERROR no has function provided!
           return False 
           
        parameters = parameter_pool.browse(cr, uid, parameter_ids, context=context)[0] 

        ftp = FTP(parameters.ftp_server)
        ftp.login(parameters.ftp_username, parameters.ftp_password)
        
        if is_k2: # FTP destination K2
            destination_path = parameters.ftp_home + "/media/k2/items/src/"
            destination_resized_path = parameters.ftp_home + "/media/k2/items/cache/"
        else: # FTP destination VM
            destination_path = parameters.ftp_home + "/images/stories/virtuemart/product/"
            destination_resized_path = parameters.ftp_home + "/images/stories/virtuemart/product/resized/"
            
        if wiz_browse.force_image:
           image_ids = product_pool.search(cr, uid, [('web','=',True)], context=context) # all web product
        else:   
           image_ids = product_pool.search(cr, uid, [('web','=',True),('web_image_update','=',True)], context=context) # only product on web and modified images
           
        i=0
        for product in product_pool.browse(cr, uid, image_ids, context=context):
            i+=1
            if i % 50 == 0:
               _logger.info('... continuing upload images, tot: %s'%(i))

            try:
                if is_k2:
                    try:
                        image = ""
                        hash_name = hash_function(product.default_code) # MD5 hash
                        for k2_type in product_pool.image_type: # for all type of images!!!
                            #image_name = product_pool.get_web_image_name(cr, uid, product.id, fullpath=False, k2_type=k2_type, context=context)  # <<< not used
                            image = product_pool.get_web_image_name(cr, uid, product.id, fullpath=True, k2_type=k2_type, context=context)   # Full path image name
                            if k2_type == "src": # default image (src folder)
                               folder = destination_path
                               image_name = hash_name + ".jpg" # TODO BRUTTISSIMA!!!!!
                            else:                # resized images all other types (cache folder + type)
                               folder = destination_resized_path
                               image_name=hash_name + "_" + k2_type + ".jpg" # TODO BRUTTISSIMA!!!!!
                                                    
                            f = open(image, "rb")
                            ftp.cwd(folder)
                            ftp.storbinary('STOR ' + image_name, f)
                            f.close()
                        # Remove check update in record image (when finish all!)
                        product_pool.write(cr, uid, product.id, {'web_image_update':False,}, context=context) 
                    except: # jumped file
                        _logger.info('Jumped file %s. Error FTP'%(image))
                               
                else:
                    try:
                        image_name = product_pool.get_web_image_name(cr, uid, product.id, fullpath=False, context=context)
                        for (image, folder) in ((product_pool.get_web_image_name(cr, uid, product.id, fullpath=True, context=context), destination_path) ,                       # Normal image (and destination)
                                                (product_pool.get_web_image_name(cr, uid, product.id, fullpath=True, resize=True, context=context), destination_resized_path)):  # Resize image (and destination)
                            f = open(image, "rb")
                            ftp.cwd(folder)
                            ftp.storbinary('STOR ' + image_name, f)
                            f.close()
                        # Remove check update in record image (only if 2 image are published!)
                        product_pool.write(cr, uid, product.id, {'web_image_update':False,}, context=context) 
                    except: # jumped file
                        _logger.info('Jumped file %s. Error FTP'%(product.name))
            except:
                log_error+="%s;"%(image_name)
                pass # no error, file still unpublished  TODO image not found!!!

        ftp.quit()        
        return log_error

    def ftp_extra_products(self, cr, uid, ids, context = None):
        ''' Pass all unpublished elements in extra product and put on the web (image files)
            Only for VM
        '''
        import ftplib
        from ftplib import FTP
        import logging
        _logger = logging.getLogger('gpb_web')
        wiz_browse=self.browse(cr, uid, ids)[0]
        extra_image_pool=self.pool.get('product.extra.photo')
        parameter_pool=self.pool.get('web.shop.parameter')

        parameter_ids = parameter_pool.search(cr, uid, [('company_id','=',1)], context=context)  # TODO parametrize

        if not parameter_ids:
           return False
           
        parameters = parameter_pool.browse(cr, uid, parameter_ids, context=context)[0] 
        
        ftp = FTP(parameters.ftp_server)
        ftp.login(parameters.ftp_username, parameters.ftp_password)
        
        #destination_path = parameters.ftp_home + "/images/stories/virtuemart/product/"
        destination_path = "~/" + parameters.ftp_home + "/images/stories/virtuemart/product/"   # as a extra path!
        
        if wiz_browse.force_image:
            image_ids = extra_image_pool.search(cr, uid, [], context=context)  # all image
        else:    
            image_ids = extra_image_pool.search(cr, uid, [('update','=',True)], context=context) # only updated

        i=0
        for image in extra_image_pool.browse(cr, uid, image_ids, context=context):
            i+=1
            if i % 50 == 0:
               _logger.info('... continuing upload extra images, tot: %s'%(i))
            try:
                image_name = extra_image_pool.get_image_name(cr, uid, image.id, complete=False, context=context)
                image_full_name = extra_image_pool.get_image_name(cr, uid, image.id, complete=True, context=context)
                f = open(image_full_name, "rb")
                ftp.cwd(destination_path)
                ftp.storbinary('STOR ' + image_name, f)
                f.close()
                
                # Remove check update in record image
                extra_image_pool.write(cr, uid, image.id, {'update':False,}, context=context) 
            except:
                _logger.info('Jumped file %s. Error FTP'%(image.name))
            
                pass # no error, file still unpublished

        ftp.quit()
        return True
        
    # Wizard button function:    
    def publish_on_web(self, cr, uid, ids, context = None):
        ''' publish on VM2.0 J2.5 via XMLRPC
        '''
        import os, tools, xmlrpclib, sys
        import logging
        _logger = logging.getLogger('gpb_web')

        _logger.info('Start Publish on web:')
        # Used pool:
        product_pool=self.pool.get('product.product')
        category_pool = self.pool.get('web.category')
        line_pool=self.pool.get('web.line')
        color_pool=self.pool.get('web.color')
        tipology_pool=self.pool.get('web.tipology')
        subtipology_pool=self.pool.get('web.subtipology')
        filter_pool=self.pool.get('web.custom.filter')
        extra_image_pool=self.pool.get('product.extra.photo')        
        parameter_pool=self.pool.get('web.shop.parameter')         
        category_k2_pool=self.pool.get('web.k2.line')  # K2 only:

        language_ids = ['en_us', 'it_it',]  # TODO parametrize (in Joomla en_us = en_gb)
        currency_type_id = "EUR" # TODO parametrize
        company_id_default = 1 #  TODO parametrize

        # Read parameter:
        parameter_ids = parameter_pool.search(cr, uid, [('company_id','=',company_id_default)], context=context)  
        if not parameter_ids:
           _logger.info('No parameter found for read configuration:')
           return False

        parameters = parameter_pool.browse(cr, uid, parameter_ids, context=context)[0] 
        #shop_proxy=shop_pool.browse(cr, uid, shop_pool.search(cr, uid, [], context=context)[0], context=context) # TODO This company
        serverphp = "%s/xmlrpc/server.php"%(parameters.web_site)
        is_k2 = parameters.company_id.k2_image_format

        # TODO Pass user name and password to xmlrpc server!
        if context is None:
           context={}

        # List to store ID created / readed
        vm_id_product={} 
        vm_id_category={} 
        vm_id_line={}    
        vm_id_color={}    
        vm_id_tipology={}
        vm_id_filters={}

        log_importation="" # TODO save in logs (or send via mail)?

        sock = xmlrpclib.ServerProxy(serverphp)

        # FILE OPERATION:
        _logger.info('Publish all photo per product on web (and resized):')
        if is_k2:           
           result=self.ftp_products(cr, uid, ids, is_k2, hash_function = sock.openerp.getImageMD5, context = context)
        else:
           result=self.ftp_category_products(cr, uid, ids, context = context)   # only for VM
           result=self.ftp_products(cr, uid, ids, is_k2, context = context)
           
        if not is_k2: #Virtuemart
            # Publish extra photo (only for VM):
            _logger.info('[INFO] Publish all extra photo per product:')
            result=self.ftp_extra_products(cr, uid, ids, context = context)
        
        # Delete extra product (removed from publish):
        _logger.info('Delete on web unpublished OpenERP product')
        vm_list_product_ids=sock.openerp.getAllProducts(is_k2) # TODO pass shop ID
        vm_product_ids={}
        if vm_list_product_ids:
            for product in product_pool.browse(cr, uid, product_pool.search(cr, uid,[('web','=',True)]), context=context):
                if product.default_code in vm_list_product_ids:
                   vm_product_ids[product.default_code]=int(vm_list_product_ids[product.default_code]) # save for product decode
                   del(vm_list_product_ids[product.default_code])
                else:
                   pass # TODO new element list!

            # delete extra element
            response=sock.openerp.deleteAllProducts(is_k2, [vm_list_product_ids[key] for key in vm_list_product_ids.keys()]) # TODO pass shop ID
        try:
            _logger.info('Start export category, shop: %s'%(serverphp))
            if is_k2: 
                # No generation of category, use this converter ID:
                log_importation += "\n[INFO] IMPORT TAG CATEGORY: *****************"
                response = sock.openerp.unlinkallCategory(is_k2) # Delete all category!
                
            else: #Virtuemart
                # * Erase all category (line and color):
                log_importation += "\n[INFO] CATEGORY IMPORTATION: *****************"
                response = sock.openerp.unlinkallCategory(is_k2)
                log_importation += "\n[INFO] Erase all categories: %s"%(response,)

                # Load dictionary for translation [category]:
                translate_category={}
                context_lang=context.get('lang','it_IT') # TODO default user?
                for language in language_ids:            
                    translate_category[language]={}
                    context['lang']=u"%s_%s"%(language[:2].lower(), language[-2:].upper())
                    for item in category_pool.browse(cr, uid, category_pool.search(cr, uid, [], context=context), context=context):
                        translate_category[language][item.id]=item.name                    
                
                # * Create root category:
                cat_filter_root_id = []
                for item in category_pool.browse(cr, uid, category_pool.search(cr, uid, [], context=context), context=context):
                    #                                      name                                  eng name                           parent order         image name         
                    response = sock.openerp.createCategory(translate_category['it_it'][item.id], translate_category['en_us'][item.id], 0, item.sequence, "category_%s.jpg"%(item.id)) 
                    vm_id_category[item.name]=int(response)
                    cat_filter_root_id.append(int(response))
                    log_importation += "\n[INFO] Create root category: %s %s "%(item.name, response)

                # Create Cat Filter element
                cat_filter_module_name = "Ricerca prodotto"   # TODO parametrize
                cat_parameter = ("%s"%(cat_filter_root_id)).replace("[","").replace("]","")
                response = sock.openerp.setCatFilter(cat_filter_module_name, cat_parameter) # ("%s"%(cat_parameter)).replace("\'","\""))
                
                # Line are restored with subcategory
                # * Create line: ***********************************************
                # Load dictionary for translation [line]:
                translate_line={}
                context_lang=context.get('lang','it_IT') # TODO default user?
                for language in language_ids:            
                    translate_line[language]={}
                    context['lang']=u"%s_%s"%(language[:2].lower(), language[-2:].upper())
                    for item in line_pool.browse(cr, uid, line_pool.search(cr, uid, [], context=context), context=context):
                        translate_line[language][item.id]=item.name                    
                
                for item in line_pool.browse(cr, uid, line_pool.search(cr, uid, [], context=context), context=context):                    
                    #                                      name                              eng name                          parent                                 order          image name         
                    response = sock.openerp.createCategory(translate_line['it_it'][item.id], translate_line['en_us'][item.id], vm_id_category[item.category_id.name], item.sequence, "line_%s.jpg"%(item.id))                     
                    vm_id_line[item.name]=int(response)
                    log_importation += "\n[INFO] Create line (subcategory): %s %s "%(item.name, response)

                # Colors are stored as category-line-colors VM category
                # * Create color: **********************************************
                # Load dictionary for translation [color]:
                translate_color={}
                context_lang=context.get('lang','it_IT') # TODO default user?
                for language in language_ids:            
                    translate_color[language]={}
                    context['lang']=u"%s_%s"%(language[:2].lower(), language[-2:].upper())
                    for item in color_pool.browse(cr, uid, color_pool.search(cr, uid, [], context=context), context=context):
                        translate_color[language][item.id]=item.name                    
                
                for item in color_pool.browse(cr, uid, color_pool.search(cr, uid, [], context=context), context=context):
                    if item.line_id and item.line_id.name in vm_id_line: # line is present and there's translation:
                        #                                      name                               eng name                           parent (present!)              order          image name         
                        response = sock.openerp.createCategory(translate_color['it_it'][item.id], translate_color['en_us'][item.id], vm_id_line[item.line_id.name], item.sequence, "color_%s.jpg"%(item.id))                     
                        vm_id_color[item.id] = int(response)   # NOTE: different from line and category that has name instead of ID
                        log_importation += "\n[INFO] Create color (sub-sub-category): %s %s "%(item.name, response)

                _logger.info('Start export manufacturer (tipology)')
                # * Erase tipology:
                log_importation += "\n[INFO] MANUFACTURER IMPORTATION: *************"
                response = sock.openerp.unlinkallManufacturer() # Erase all mf
                log_importation += "\n[INFO] Erase all mf: %s"%(response)

                # Load dictionary for translation [tipology]:
                translate_tipology={}
                context_lang=context.get('lang','it_IT') # TODO default user?
                for language in language_ids:            
                    translate_tipology[language]={}
                    context['lang']=u"%s_%s"%(language[:2].lower(), language[-2:].upper())
                    for item in tipology_pool.browse(cr, uid, tipology_pool.search(cr, uid, [], context=context), context=context):
                        translate_tipology[language][item.id]=item.name                    

            
            if not is_k2: # Only for Virtuemart
                # * Create tipology:
                for item in tipology_pool.browse(cr, uid, tipology_pool.search(cr, uid, [], context=context), context=context): # Create all mf
                    response = sock.openerp.createManufacturer(translate_tipology['it_it'][item.id], translate_tipology['en_us'][item.id])
                    vm_id_tipology[item.name]=int(response)
                    log_importation += "\n[INFO] Created manufacturer: %s %s"%(item.name, response)

                _logger.info('Start export custom fields')
                # * Create custom fields:
                # Language translation TODO (via file)
                '''
                ; Virtuemart! Project
                ; Copyright (C)  2011 Virtuemart Team. All rights reserved.
                ; License http://www.gnu.org/licenses/gpl-2.0.html GNU/GPL, see LICENSE.php
                ; Note : All ini files need to be saved as UTF-8 - No BOM
                ;
                COM_VIRTUEMART_ACC_BILL_DEF="- Default (Lo stesso della fatturazione)"

                '''

                            
            if not is_k2:  # Only for Virtuemart                
                log_importation += "\n[INFO] CUSTOM FIELDS IMPORTATION: ************"
                response = sock.openerp.createCustoms("Linea", 0, 1) # first order (list)
                vm_id_filters["Linea"] = int(response)

                for item  in filter_pool.browse(cr, uid, filter_pool.search(cr, uid, [], context=context), context=context):
                    response = sock.openerp.createCustoms(item.name, item.sequence, item.field_type) 
                    vm_id_filters[item.name] = int(response)
                    log_importation += "\n[INFO] Create custom field: %s %s"%(item.name, response)

            _logger.info('Start export products')
            # * Import product:
            product_total=0 
            log_importation += "\n[INFO] PRODUCT IMPORTATION: ******************"

            if is_k2: 
               # Create new product (or update):               
               # Nota, quando creo: vm_product_ids[product.default_code] 
               product_browse = product_pool.browse(cr, uid, product_pool.search(cr, uid,[('web','=',True)], order='vm_name', context=context), context=context)
               for product in product_browse:
                    product_total+=1 # and order
                    if product_total % 50 == 0: # log every 50 product exported
                       _logger.info('Partial exported product: %s'%(product_total))
                    response = sock.openerp.createK2Products(product.default_code,               # code   (used for test if exist (update or create)
                                                             product.vm_name or product.name,    # name
                                                             k2_parameters, #product.k2_params or "",                  # params  (use default string)
                                                             "",#product.k2_gallery or "",                 # gallery
                                                             self.get_k2_extra_fields(cr, uid, product),
                                                             # << TODO generate *****************************
                                                             product.k2_extra_field_search or "",      # extra search
                                                             product.k2_image_caption or "",           # image caption
                                                             "",#product.k2_introtext or "",               # introtext
                                                             "",#product.k2_fulltext or "",                # full text
                                                             product_total or 0,                       # ordering
                                                             1 if product.k2_all_product else 3)       # if check=1 (all) else 3 (accessory)
                                                             
                    #vm_product_id = response                    
                    vm_product_ids[product.default_code] = int(response)   # for create extra fields after
                    if not vm_product_ids[product.default_code]:
                       _logger.info('Not created: %s'%(product.vm_name or product.name))

               # Create tag category element: 
               tag_category={'Tavoli e Sedie':8, 'Arredo giardino':2, 'Interno':3, 'Campeggio':5, 'Accessori e Ricambi':9, 'Mare e piscina':12} # TODO dinamically?
               for item in category_k2_pool.browse(cr, uid, category_k2_pool.search(cr, uid, [], context=context), context=context):
                   if item.category_id.name in tag_category and item.product_id.default_code in vm_product_ids: 
                       response = sock.openerp.createK2Tag(tag_category[item.category_id.name], vm_product_ids[item.product_id.default_code]) 
                   else:
                       pass   # not find category or product! TODO error??

               # Create vetrina product:
               _logger.info('Export Home vetrina product')
               vetrina_pool=self.pool.get('web.k2.vetrina')
               for vetrina in vetrina_pool.browse(cr, uid, vetrina_pool.search(cr, uid, [], context=context), context=context):
                    response = sock.openerp.createVetrina(vetrina.k2_id,
                                                          vm_product_ids[vetrina.product_id.default_code],
                                                          vetrina.badge)
               # Publish Custom mod for product:                   
               _logger.info('Export Custom mod for product')
               mod_custom_pool=self.pool.get('web.k2.mod.custom')
               for mc in mod_custom_pool.browse(cr, uid, mod_custom_pool.search(cr, uid, [], context=context), context=context):
                    response = sock.openerp.createProductModCustom(mc.k2_id or 0,
                                                                   mc.name,
                                                                   mc.text,
                                                                   "1" if mc.has_title else "0",
                                                                   )
                    if not mc.k2_id: # update ID in Openerp
                       update_response = mod_custom_pool.write(cr, uid, mc.id, {'k2_id': int(response)}, context=context)

               # Publish Gallery for product image K2:                   
               _logger.info('Export K2 gallery')
               gallery_pool=self.pool.get('web.k2.gallery')
               for gallery in gallery_pool.browse(cr, uid, gallery_pool.search(cr, uid, [], context=context), context=context):
                    response = sock.openerp.createProductGallery(gallery.name,        # folder (unique)
                                                                 gallery.long_title,  # title of gallery
                                                                 )
                    if response:  # to not reset ID if update errors
                       update_response = gallery_pool.write(cr, uid, gallery.id, {'k2_id': int(response)}, context=context)
                    if gallery.publish: # publish FTP all gallery 
                       self.ftp_k2_gallery(cr, uid, ids, gallery.name, context = context)     # publish images for this gallery                  

                       update_response = gallery_pool.write(cr, uid, gallery.id, {'publish': False}, context=context)
                       
               
               # TODO link menuitem to custom modules
               _logger.info('Export K2 gallery and custom module on product')
               for product in product_browse:
                   # delete all record for product code, usefull both for custom and gallery:
                   response = sock.openerp.deleteK2MenuitemModule(product.default_code)
                   for custom in product.k2_mod_custom_ids:
                       response = sock.openerp.createK2MenuitemModule(product.default_code,      # code (in php is transformed in menuitem)
                                                                      custom.k2_id,              # module ID in K2
                                                                      )  
                   if product.k2_gallery_id:                                            
                      response = sock.openerp.createK2MenuitemGallery(product.default_code,          # code (in php is transformed in menuitem)
                                                                      product.k2_gallery_id.k2_id,   # gallery ID in K2
                                                                      )                       
                                       
            else: #Virtuemart
                # Load dictionary for translation [product]:
                context_lang=context.get('lang','it_IT') # TODO default user?
                translation = {}
                for language in language_ids: # TODO parametrize and insert search with context lang_id!
                   translation[language] = {}
                   context['lang']=u"%s_%s"%(language[:2].lower(), language[-2:].upper())
                   for product in product_pool.browse(cr, uid, product_pool.search(cr, uid,[('web','=',True)]), context=context):            
                       translation[language][product.id]=(product.vm_name or product.default_code,   # name
                                                               product.vm_short or product.name[8:],          # short
                                                               product.large_description or "",) #product.vm_description or "",)                 # description TODO find what!!!!
                context['lang'] = context_lang # restore previous lang

                
                for product in product_pool.browse(cr, uid, product_pool.search(cr, uid,[('web','=',True)]), context=context):
                    product_total+=1
                    if product_total % 50 == 0: # log every 50 product exported
                       _logger.info('Partial exported product: %s'%(product_total))
                       
                    # insert product (or update) ***********************************
                    response = sock.openerp.createProducts(product.default_code,                                                 # code
                                                           "%2.2f"%(product.price),                                              # price   TODO mettere a parte
                                                           vm_id_category.get(product.category_id.name, 0),                      # category ID   (now product are under line=subcategory)
                                                           vm_id_line.get(product.line_id.name, 0),                              # line ID
                                                           vm_id_color.get(product.color_id.id, 0) if product.color_id else 0,   # color ID
                                                           vm_id_tipology.get(product.tipology_id.name, 0),                      # tipology ID
                                                           currency_type_id,                                                     # type of price (ex. EUR) TODO terminare la gestione dei prezzi (non viene visualizzato per ora)
                                                           product.weight,                                                       # weight
                                                           product.length,                                                       # length   # NON ESISTE IN FIAM
                                                           product.width,                                                        # width 
                                                           product.height)                                                       # height
                    #if product.weight or product.length or product.width or product.height:
                    vm_product_id = response

                    # Create language
                    for language in language_ids: # TODO parametrize and insert search with context lang_id!                    
                        language_meta=language
                        if language=="en_us":
                           language_meta="en_gb"
                        response = sock.openerp.createProductsLanguage(language_meta,                               # Lang code (ex. it_it or en_gb)
                                                                       vm_product_id,                          # VM product ID
                                                                       translation[language][product.id][0],   # name
                                                                       translation[language][product.id][1],   # short
                                                                       translation[language][product.id][2],)  # description TODO find what!!!!
                    
                    vm_id_product[product.default_code]=vm_product_id # save for linked product
                    
                    log_importation += "\n[INFO] Creata product: %s %s"%(product.name, response)

                    # MANAGE MEDIA ELEMENTS: ***************************************
                    # MEDIA (PRODUCT IMAGE):****************************************
                    response = sock.openerp.createMedia("%s.jpg"%(product.default_code))           # ex.: 00100.jpg        
                    vm_media_id=int(response)
                    log_importation += "\n[INFO]            Create media: %s.jpg %s"%(product.default_code, response)

                    # MEDIA PRODUCT: ***********************************************
                    response = sock.openerp.unlinkProductMedia("%d"%(vm_product_id))  # Delete all (usafull also for extra image)
                    log_importation += "\n[INFO]            Erase all media product association: %s"%(response)
                    response = sock.openerp.createProductMedia(vm_product_id,
                                                               vm_media_id,
                                                               0) # First record of the list of media
                    log_importation += "\n[INFO]            Create media product: %s.jpg %s"%(product.default_code, response)

                    # MEDIA (EXTRA PRODUCT IMAGE):****************************************
                    # Product uploaded at start with FTP copy:
                    for extra_image in product.extra_photo_ids:
                        # Create media:
                        image_name=extra_image_pool.get_image_name(cr, uid, extra_image.id, complete=False, context=context)
                        response = sock.openerp.createMedia(image_name)           # ex.: 00100.a.01.jpg        
                        vm_extra_id=int(response)
                        log_importation += "\n[INFO]            Create media for extra image [product]: %s %s"%(image_name, response)

                        # Create link media-product for extra product (no erase, previously do it):
                        response = sock.openerp.createProductMedia(vm_product_id,
                                                                   vm_extra_id,
                                                                   1) # TODO (ordered??)
                        log_importation += "\n[INFO]            Create media link extra image-product: %s [%s]"%(image_name, response)                    

                    # insert custom filter: ************************************************                
                    #   delete all filter for product:
                    response = sock.openerp.unlinkCustomFilter("%d"%(vm_product_id))  
                    log_importation += "\n[INFO] Erase all product custom filters: %s"%(response)
                    
                    #   create all filter for tipology:
                    for st_id in product.subtipology_ids:
                        if st_id.name and st_id.custom_filter_id:  # TODO DEBUG
                            response = sock.openerp.createCustomFilter(st_id.name,                                                  # name
                                                                   "%d"%(vm_product_id),                                            # VM product_id
                                                                   "%d"%(vm_id_filters.get(st_id.custom_filter_id.name, "")))       # VM filter_id
                            log_importation += "\n[INFO]     Create custom filter %s product: %s ID %s"%(st_id.name, product.name, response)

            if not is_k2: # Only for Virtuemart: 
                # Linked product (all web product with some children link) NOTE: all vm_product_cf are previously deleted in this proc!:
                _logger.info('Import linked product')
                for product in product_pool.browse(cr, uid, product_pool.search(cr, uid,[('web','=',True),('parent_ids','!=',False)]), context=context):
                    for child in product.parent_ids:
                        if child.child_id.default_code in vm_id_product:  # only if I have ID (else no web published)
                           response = sock.openerp.createCustomRelatedFilter(vm_id_product[product.default_code], 
                                                                             vm_id_product[child.child_id.default_code], 
                                                                             child.sequence)   # TODO ordering?
                           log_importation += "\n[INFO]            Create linked child product: parent: %s child: %s [%s]"%(product.default_code, child.child_id.default_code, response)
                        else:
                           log_importation += "\n[WARN]            Jump product linked: P: %s C: %s"%(product.default_code, child.child_id.default_code)
                        
            _logger.info('End exportation!')
        except Exception, e:
            log_importation += "\n[ERR] Generic error: %s"%(e)
            _logger.error('Generic error during VM export: %s' % (e,))            
       
        return {'type' : 'ir.actions.act_window_close'}

    _columns = {
                'name': fields.char('Name', size=64, required=False, readonly=False),
                'force_image': fields.boolean('Force image', required=False, help="Force image not watch the timestamp value"),
    }    
    _defaults = {
        'force_image': lambda *a: False,
    }
web_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
