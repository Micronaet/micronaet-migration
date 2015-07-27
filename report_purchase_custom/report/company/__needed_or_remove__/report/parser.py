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

from report import report_sxw
from report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_volume_item':self.get_volume_item,
            'total_volume':self.total_volume,
            
            'get_price': self.get_price,
            'get_subtotal': self.get_subtotal,
            'get_total': self.get_total,

            'total_USD':self.total_USD,
            'get_couple': self.get_couple,
        })

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
                return "%2.2f"%(float("%2.2f"%(item.product_id.seller_ids[0].pricelist_ids[0].price)) * item.product_qty)
            elif currency == "USD":
                return "%2.2f"%(float("%2.2f"%(item.product_id.seller_ids[0].pricelist_ids[0].price_usd)) * item.product_qty)
        except:
            pass # on error price is empty    
        return "0.0"  
        
    def get_total(self, items, order):
        total=0.0
        for item in items:
            total += float(self.get_subtotal(item, order))
        return "%2.2f"%(total)
        
    def get_total_volume(self, item_list):
        ''' Function that compute total volume for 1 or more items
        '''
        total = 0.0
        for item in self.pool.get('purchase.order.line').browse(self.cr, self.uid, item_list):
            if item.product_id and len(item.product_id.packaging)==1 and item.product_id.packaging[0].qty:  # only one package!
                #     total order      / total per box                     1 box if there's a rest            
                box = item.product_qty // item.product_id.packaging[0].qty + (0.0 if item.product_qty % item.product_id.packaging[0].qty == 0.0 else 1.0) 
                volume = item.product_id.packaging[0].pack_volume if item.product_id.packaging[0].pack_volume_manual else (item.product_id.packaging[0].length *
                                                                                                                           item.product_id.packaging[0].width *
                                                                                                                           item.product_id.packaging[0].height) / 1000000.0
                total_value =  box * volume
                total += float("%2.3f"%(total_value))  # for correct aprox value (maybe theres' a best way :) )
        return "%2.3f"%(total,)
        
    def get_volume_item(self, item_id):
        ''' calculate total volume for item line 
            Pz / Pz. x box * (volume of the box => l x w x h)
        '''
        return self.get_total_volume([item_id])
        
    def total_volume(self, order_id):
        ''' calculate total volume for all items present in order
        '''
        item_list = self.pool.get('purchase.order').browse(self.cr, self.uid, order_id).order_line
        if item_list:
            return self.get_total_volume([item.id for item in item_list])
        return ""    

    def total_USD(self, order_id):
        ''' calculate total USD for all items present in order
        '''
        total=0.0
        for item in self.pool.get('purchase.order').browse(self.cr, self.uid, order_id).order_line:
            if item.product_id and item.product_id.fob_cost_supplier:
                total += float("%2.2f"%(item.product_id.fob_cost_supplier,)) * item.product_qty
        return "%2.2f"%(total,)

