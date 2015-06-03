##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
# Modified template model from:
#
# Micronaet s.r.l. - Nicola Riolini
# Using the same term of use
##############################################################################

from osv import osv, fields
from datetime import datetime
import decimal_precision as dp
import tools, os
import base64, urllib

class inherit_product_product(osv.osv):
    _name = 'product.product'
    _inherit = 'product.product'

    def get_quotation_image(self, cr, uid, item, context=None):
        ''' Get single image for the file
            (default path is ~/photo/db_name/quotation
        '''        
        img = ''         
        extension = "jpg"
        image_path = os.path.expanduser("~/photo/%s/product/default"%(cr.dbname))
        empty_image= "%s/%s.%s"%(image_path, "empty", extension)

        product_browse=self.browse(cr, uid, item, context=context)
        # Image compoesed with code format (code.jpg)
        if product_browse.default_code:
            try:
                (filename, header) = urllib.urlretrieve("%s/%s.%s"%(image_path, product_browse.default_code.replace(" ", "_"), extension)) # code image
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            
            if not img: # empty image:
                try:
                    (filename, header) = urllib.urlretrieve(empty_image) # empty setted up on folder
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''
        return img

    # Fields function:
    def _get_quotation_image(self, cr, uid, ids, field_name, arg, context=None):
        ''' Field function, for every ids test if there's image and return
            base64 format according to code value (images are jpg)
        '''
        res = {}
        for item in ids:
            res[item] = self.get_quotation_image(cr, uid, item, context=context)
        return res                

    _columns = {
                'quotation_photo':fields.function(_get_quotation_image, type="binary", method=True),
                'quantity_x_pack': fields.integer('Q. per pack'),
               }                
    _defaults = {
        'quantity_x_pack': lambda *a: 1,
    }               
inherit_product_product()

class sale_order_extra(osv.osv):
    """
    sale.order extra fields
    """
    _inherit = 'sale.order'
    _name = 'sale.order'
    
    _columns = {
        'quotation_model':fields.selection([(1,'Offerta dettagliata (q.-sconto-subtotali)'),
                                            (2,'Offerta breve (solo q.)'),],'Model', readonly=False, required=True),
    }
    _defaults = {
        'quotation_model': lambda *x: 2, # short
    }    
sale_order_extra()

class sale_order_line_add_fields(osv.osv):
    _name='sale.order.line'
    _inherit='sale.order.line'
    
    _columns={
             'repeat_header_line': fields.boolean('Intest.', required=False, help="Spuntare quando e' richiesta l'intestazione, tipo dopo una riga titolo."),             
             'insert_photo': fields.boolean('Con foto', required=False, help="Spuntare quando e' richiesto l'inserimento della foto a preventivo."),                                     
             'use_amazon_description': fields.boolean('Amazon description', required=False, help="Take amazon description instead of product's one"),
             'show_notes': fields.boolean('Show notes', required=False, help="Show notes after description"),
             }
sale_order_line_add_fields()
