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

from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_volume_item':self.get_volume_item,
            'get_q_x_pack': self.get_q_x_pack,
            'get_supplier_code': self.get_supplier_code,
            
            # Multi pack insert depend on Campaign module:
            'multipack_dimension_list': self.multipack_dimension_list,
            'multipack_dimension_volume': self.multipack_dimension_volume,            
            'multipack_dimension_volume_total': 
                self.multipack_dimension_volume_total,
            
            # TODO remove:
            'total_volume':self.total_volume,
            'get_total_volume':self.get_total_volume,
            'get_unit_volume':self.get_unit_volume,
            
            'get_price': self.get_price,
            'get_subtotal': self.get_subtotal,
            'get_total': self.get_total,
            'get_lang_field': self.get_lang_field,

            'total_USD':self.total_USD,
            'get_couple': self.get_couple,
            })

    # -------------------------------------------------------------------------
    # Multipack block:
    # -------------------------------------------------------------------------
    # Utility:
    def multipack_extract_info(self, detail, data='list'):
        ''' Extract data from product detail
            data:  
                'list' for list of elements
                'volume' volume total
                'total' volume total
            
        '''
        res = []
        volume = 0
        product = detail.product_id
        qty= detail.product_qty or 0
        if product.has_multipackage:
            for pack in product.multi_pack_ids:
                for loop in range(0, pack.number or 1):
                    res.append('%s x %s x %s' % (
                        pack.height, pack.width, pack.length,
                        ))
                    volume_1 = pack.height * pack.width * pack.length / 1000000.0
                    if data == 'total':    
                        volume += qty * volume_1
                    elif data == 'volume':
                        volume += volume_1
        else:
            res.append('%s x %s x %s' % (
                product.pack_l, product.pack_h, product.pack_p
                ))
            q_x_pack = self.get_q_x_pack(product)
            volume_1 = \
                product.pack_l * product.pack_h * product.pack_p / 1000000.0
            if data == 'volume':
                volume = volume_1
            elif data == 'total':
                volume = qty * volume_1 / q_x_pack
                            
        if data == 'list':
            return res                
        # elif 'volume':
        return volume
        
    # Get pack list:
    def multipack_dimension_list(self, detail, as_list=True):
        ''' Create list of elements
            return as_list or as text formatted
        '''
        res = self.multipack_extract_info(detail, data='list')
        if as_list:
            return '\n'.join(res)
        else:    
            return res

    # Get volume
    def multipack_dimension_volume(self, detail, data='volume'):
        ''' Calculate volume multipack or product pack data
            data: 'volume' for one 'totat' for total
        '''
        volume = self.multipack_extract_info(detail, data=data)
        return '%2.3f' % volume

    # Get total volume
    def multipack_dimension_volume_total(self, order):
        ''' Get total volume        
        '''
        volume = 0.0
        for detail in order.order_line:
            volume += self.multipack_extract_info(detail, data='total')
        return '%2.3f' % volume

    def get_q_x_pack(self, product):
        # Old method after where saved here
        if product.has_multipackage:
            return 1
        elif len(product.packaging_ids) == 1:
            return int(product.packaging_ids[0].qty or 1.0)
        else:
            return int(product.q_x_pack or 1)
    # -------------------------------------------------------------------------
        
    def get_supplier_code(self, product):        
        if product.default_supplier_code:
            return '[%s]' % (product.default_supplier_code)
        elif product.seller_ids and product.seller_ids[0].product_code:
            return '[%s]' % (product.seller_ids[0].product_code)
        else:
            return '/'
            
    def get_lang_field(self, pool, item_id, field, lang):
        ''' Get field from obj in lang passed
        ''' 
        context = {'lang': lang}
        obj_pool = self.pool.get(pool)
        obj_proxy = obj_pool.browse(self.cr, self.uid, item_id, context=context)
        return obj_proxy.__getattribute__(field)
            

    def get_couple(self, order_line):
        ''' Couple the elements
        '''
        res = []

        position = 0 # next is 0
        for element in order_line:
            # Colls:
            try:
                colls = int(element.product_id.colls) or 1
            except:
                colls = 1 # error in conversion    
            
            # Q x Pack.    
            try:
                q_x_pack = int(element.product_id.q_x_pack) or '/'
            except:
                q_x_pack = '/' # error in conversion    

            for i in range(1, colls + 1):
                position += 1
                part_number = "%s/%s" % (i, colls)
                if position % 2 == 1: # odd
                    # fist element:
                    res.append([
                        [element, part_number, q_x_pack],
                        [False, False, False]
                        ])
                else: # event
                    # second element:
                    res[(position-1) / 2][1][0] = element 
                    res[(position-1) / 2][1][1] = part_number
                    res[(position-1) / 2][1][2] = q_x_pack                    
        return res

    def get_price(self, item, order):
        ''' Return cost price from pricelist in currency indicated
        '''
        try: 
            currency = order.partner_id.property_product_pricelist_purchase.currency_id.name
            if currency == "EUR":
                return "%2.2f"%(item.product_id.seller_ids[0].pricelist_ids[0].price,)
            elif currency == "USD":
                return "%2.2f"%(item.product_id.seller_ids[0].pricelist_ids[0].price_usd,)
        except:
            pass # on error price is empty    
        return "0.0"    
        
    def get_subtotal(self, item, order):
        try:
            currency = order.partner_id.property_product_pricelist_purchase.currency_id.name
            if currency == "EUR":
                return "%2.2f"%(float("%2.2f"%(
                    item.product_id.seller_ids[
                        0].pricelist_ids[0].price)) * item.product_qty)
            elif currency == "USD":
                return "%2.2f"%(float("%2.2f"%(
                    item.product_id.seller_ids[
                        0].pricelist_ids[0].price_usd)) * item.product_qty)
        except:
            pass # on error price is empty    
        return "0.0"  
        
    def get_total(self, items, order):
        total=0.0
        for item in items:
            total += float(self.get_subtotal(item, order))
        return "%2.2f"%(total)

    def get_unit_volume(self, item):
        ''' get unit volume
        '''
        #if len(item.product_id.packaging_ids) == 1:                
        return "%2.3f" % ((
            item.product_qty * \
            item.product_id.pack_l * \
            item.product_id.pack_h * \
            item.product_id.pack_p / 1000000.0 / (
                self.get_q_x_pack(item.product_id))) or 0.0)
        #else:
        #    return '/'
                                
    def get_total_volume(self, o):
        ''' Function that compute total volume for 1 or more items
        '''
        res = 0.0
        for item in o.order_line:
            #if len(item.product_id.packaging_ids) == 1:                
            res += (item.product_qty * \
                item.product_id.pack_l * \
                item.product_id.pack_h * \
                item.product_id.pack_p / 1000000.0 / (
                    self.get_q_x_pack(item.product_id))) or 0.0
        return '%2.3f' % res           
            
    def get_volume_item(self, item_id):
        ''' calculate total volume for item line 
            Pz / Pz. x box * (volume of the box => l x w x h)
        '''
        return self.get_total_volume([item_id])
        
    def total_volume(self, o):
        ''' calculate total volume for all items present in order
        '''
        return  '' #self.get_total_volume([item.id for item in item_list])

    def total_USD(self, order_id):
        ''' calculate total USD for all items present in order
        '''
        total=0.0
        for item in self.pool.get('purchase.order').browse(self.cr, self.uid, order_id).order_line:
            if item.product_id and item.product_id.fob_cost_supplier:
                total += float("%2.2f"%(item.product_id.fob_cost_supplier,)) * item.product_qty
        return "%2.2f"%(total,)

