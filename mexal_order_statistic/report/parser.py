# -*- coding: utf-8 -*-
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

last_record = 0

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'product_list':self.product_list,
            'colli_total':self.colli_total,
            'orders':self.order_browse,
            'total_orders':self.total_orders, 
            'is_last': self.is_last,
            'reset_print':self.reset_print,
            'get_telephone': self.get_telephone,
            'get_address_default': self.get_address_default,
            'italian_date':self.get_italian_date,
        })

    def is_last(self, item_id):
        ''' Test if the record id passed is the last of the list
        '''
        global last_record
        if not (item_id and last_record):
            return False
        return item_id==last_record  # return test value
            
        if value:
            return "%s-%s-%s"%(value[8:10],value[5:7],value[:4],)
        return ""
        

    def get_italian_date(self, value):
        if value:
            return "%s-%s-%s"%(value[8:10],value[5:7],value[:4],)
        return ""
        
    def get_telephone(self, ids):
        if not ids:
           return ""
           
        partner_proxy=self.pool.get('res.partner').browse(self.cr, self.uid, ids)
        for address in partner_proxy.address:
            if not address.mexal_c and not address.mexal_s: # no address destination and supplier
               return address.phone
        return ""

    def get_address_default(self, item_id, partner_name = ""):
        ''' Get, from id of partner the first default address imported 
        '''
        if not item_id:
            return ""
           
        partner_address_pool=self.pool.get('res.partner.address')
        find_ids = partner_address_pool.search(self.cr, self.uid, [('partner_id','=',item_id),('type','=','default'),('import','=',True)])
        
        if not find_ids:
            return partner_name
            
        partner_address_proxy = partner_address_pool.browse(self.cr, self.uid, find_ids)[0] # take first
        return "%s\n%s\n%s - %s"%(partner_address_proxy.partner_id.name, partner_address_proxy.street, partner_address_proxy.zip, partner_address_proxy.city)

    def reset_print(self):
        ''' Called at the end of report to reset print check
        '''
        # Azzero tutte le selezioni (al termine della stampa:
        header_ids=self.pool.get('statistic.header').search(self.cr, self.uid, [('print','=',True)])
        header_mod=self.pool.get('statistic.header').write(self.cr, self.uid, header_ids, {'print': False})     
        return "" # print nothing    

    def total_orders(self, objects):
        ''' true if the order list is more than one
        '''
        active_ids_list= [x.id for x in objects]        
        order_ids = self.pool.get('statistic.header').search(self.cr, self.uid, [('print', '=', True),])
        return len(list(set(active_ids_list + order_ids)) )

    def _get_fully_list(self, objects):
        ''' return list of object browse id list merged with no replication with
            al record masked for print 
        '''
        active_ids_list= [x.id for x in objects]        
        order_ids = self.pool.get('statistic.header').search(self.cr, self.uid, [('print', '=', True),])
        total_list = list(set(active_ids_list + order_ids)) # lista senza dublicati di ID
        return total_list
        
    def order_browse(self, objects):
        ''' Return only in_pricelist product for print a pricelist
        '''
        #import pdb; pdb.set_trace()
        global last_record
        last_record = 0
        
        ids=self._get_fully_list(objects)
        order_proxy=self.pool.get('statistic.header').browse(self.cr, self.uid, ids) 
        
        last_record=ids[-1] # for extra page
        return order_proxy
        
    def colli_total(self, order_id):
        total=0
        order_line_ids=self.pool.get('statistic.order').search(self.cr, self.uid, [('header_id', '=', order_id)])
        
        for order_line in self.pool.get('statistic.order').browse(self.cr, self.uid, order_line_ids):
            if order_line.colli:
               total += order_line.colli or 0
            else:
               total += order_line.quantity or 0
        return total    

    def product_list(self, objects):
        products = {}
        for order in self.pool.get('statistic.header').browse(self.cr, self.uid, self._get_fully_list(objects)):
            for item in order.line_ids:            
                if item.line_type != "d": # only article lines
                    if item.code in products:
                        products[item.code][0] += item.quantity or 0.0
                        products[item.code][1] += item.quantity_ok or 0.0
                        products[item.code][2] = item.article or "" # tolto il + (metteva più righe)
                    else:          
                        products[item.code] = [item.quantity or 0.0, item.quantity_ok or 0.0, item.article or ""]
       
        products_sorted = []       
        for k in sorted(products.iterkeys()):
            products_sorted.append([k, products[k][0], products[k][1], products[k][2]])
        return products_sorted
