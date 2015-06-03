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

class product_product_merger(osv.osv):
    ''' Override mapping procedure
    '''    
    _name = 'product.product'
    _inherit = 'product.product'

    # button event:
    def button_replicate_parent(self, cr, uid, ids, context=None):
        ''' Button event that copy title, description and function in all product
            child, ex.: parent 005, copied in 005TX ecc. ecc.
        '''        
        import os
        f = open(os.path.expanduser("~/log.txt"), "a") # log operations
        f.write("\n" + "*"*20)

        parent = self.browse(cr, uid, ids, context=context)[0]
        child_ids=self.search(cr, uid, [('default_code', 'like', parent.default_code + "%")], context=context)  # product with a part of code
        temp = self.read(cr, uid, child_ids, ('default_code',), context=context)  # debug
        
        for product in self.browse(cr, uid, child_ids, context=context):
            if ((not product.amazon_mig_title or 
                 not product.amazon_mig_description or 
                 not product.amazon_mig_material or 
                 not product.amazon_mig_keywords or 
                 not product.amazon_mig_category1_id or 
                 not product.amazon_mig_category2_id or 
                 not product.amazon_mig_volume_um or
                 #not product.amazon_mig_volume or 
                 not product.volume or
                 not product.amazon_mig_price or 
                 not product.amazon_mig_weight_um or 
                 not product.amazon_mig_weight or 
                 not product.weight_net or 
                 not product.amazon_mig_dimension_um or 
                 not product.amazon_mig_length or 
                 not product.amazon_mig_width or 
                 not product.amazon_mig_height or 
                 not product.amazon_mig_function) and 
                 len(parent.default_code) < len(product.default_code) and
                 product.default_code[:len(parent.default_code)] == parent.default_code):
               data={}  
               if not product.amazon_mig_title: data['amazon_mig_title']=parent.amazon_mig_title
               if not product.amazon_mig_description: data['amazon_mig_description']=parent.amazon_mig_description
               if not product.amazon_mig_material: data['amazon_mig_material']=parent.amazon_mig_material
               if not product.amazon_mig_keywords: data['amazon_mig_keywords']=parent.amazon_mig_keywords
               if not product.amazon_mig_category1_id: data['amazon_mig_category1_id']=parent.amazon_mig_category1_id.id
               if not product.amazon_mig_category2_id: data['amazon_mig_category2_id']=parent.amazon_mig_category2_id.id
               if not product.amazon_mig_volume_um: data['amazon_mig_volume_um']=parent.amazon_mig_volume_um
               if not product.volume: data['volume']=parent.volume
               if not product.amazon_mig_price: data['amazon_mig_price']=parent.amazon_mig_price
               if not product.amazon_mig_weight_um: data['amazon_mig_weight_um']=parent.amazon_mig_weight_um
               if not product.amazon_mig_weight: data['amazon_mig_weight']=parent.amazon_mig_weight
               if not product.weight_net: data['weight_net']=parent.weight_net
               if not product.amazon_mig_dimension_um: data['amazon_mig_dimension_um']=parent.amazon_mig_dimension_um
               if not product.amazon_mig_length: data['amazon_mig_length']=parent.amazon_mig_length
               if not product.amazon_mig_width: data['amazon_mig_width']=parent.amazon_mig_width
               if not product.amazon_mig_height: data['amazon_mig_height']=parent.amazon_mig_height
               if not product.amazon_mig_function == False: data['amazon_mig_function']=parent.amazon_mig_function
               modify=self.write(cr, uid, product.id, data)                   
               f.write("\nfrom %s to %s"%(parent.default_code, product.default_code))
        f.close()    
        return True

    def mapping_data_record(self, cr, uid, product, context=None): 
        ''' Override function with mapping fields
        '''
        res = {               
               #'amazon_q_x_pack': product.q_x_pack,
               'amazon_volume': product.volume,
               'amazon_weight': product.weight_net,
              }
        
        return res
product_product_merger()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
