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

    def mapping_data_record(self, cr, uid, product, context=None): 
        ''' Override function with mapping fields
        '''
        res = {               
               #'amazon_color': product.colour,
               #'amazon_material': product.fabric,
               #'amazon_description': product.description_sale,
               'amazon_length': product.length,
               'amazon_width': product.width,
               'amazon_height': product.height,
               'amazon_volume': product.volume,
               'amazon_weight': product.weight_net,
              }        
        return res
product_product_merger()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
