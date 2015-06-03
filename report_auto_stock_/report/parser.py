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
    jump_list=[]
    
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'product_auto_list': self.product_auto_list(),
            'jump_page': self.jump_page,
        })

    def product_auto_list(self):
        ''' Read all mexal code (to search required products)
            Order and produce a pseudo objects with browse object
            for generate automatically PDF print
        '''
        global jump_list
        jump_list=[]
        supplier_ids=self.pool.get('auto.stock.supplier').search(self.cr, self.uid, []) # all elements
        supplier_code_ids= [item['name'] for item in self.pool.get('auto.stock.supplier').read(self.cr, self.uid, supplier_ids)]
        
        active_ids=self.pool.get('statistic.store').search(self.cr, self.uid, [('company','=','gpb'),('mexal_s', 'in', supplier_code_ids)], order='mexal_s,product_code')
        objects=self.pool.get('statistic.store').browse(self.cr, self.uid, active_ids)
        last=""
        for item in objects:
            if not last or last!=item.mexal_s:
               last=item.mexal_s
               jump_list.append(item.id)   
        return objects

    def jump_page(self, item_id):
        global jump_list
        return item_id in jump_list
