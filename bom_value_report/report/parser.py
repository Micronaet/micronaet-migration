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
            'min_value':self.get_min_value,
            'max_value':self.get_max_value,
            'sort_browse': self.sort_browse,
        })

    def sort_browse(self, obj):
        ''' Sort browse object
        '''
        res = {}
        for item in obj:
            res[item.product_id.default_code] = item
        
        result = []
        for key in sorted(res):
            result.append(res[key])
        return result
        
    def get_value(self, bom_id, type_of="min"):
        components=self.pool.get('mrp.bom').browse(self.cr, self.uid, bom_id)
        tot=0
        note=""
        #uom=components.product_uom.name
        for component in components.bom_lines:             # loop on component
            value=0                
            for seller in component.product_id.seller_ids: 
                for pricelist in seller.pricelist_ids:     
                    if pricelist.price > 0 and pricelist.is_active:
                       if type_of=="min":   
                          if not value: 
                             value=pricelist.price
                          if pricelist.price < value: 
                             value=pricelist.price
                       else: # suppose max
                          if pricelist.price > value: 
                             value=pricelist.price
            if not value:
               note="**"              
            tot+= value * component.product_qty  # compute Q * min price              
        return "%s %.5f %s" % (note, tot, "EUR")

    def get_min_value(self, bom_id):
        return self.get_value(bom_id, "min")
        
    def get_max_value(self, bom_id):
        return self.get_value(bom_id, "max")
