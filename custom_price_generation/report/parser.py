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
        self.context=context
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'obj_product': self.obj_product,
        })

    def obj_product(self):
        '''Return only in_pricelist product for print a pricelist
        '''
        #import pdb; pdb.set_trace()
        product_ids=self.pool.get('product.product').search(self.cr, self.uid, [('in_pricelist', '=', True),])
        #product_proxy=self.pool.get('product.product').read(self.cr, self.uid, product_ids, ['id', 'name', 'code',])
        product_proxy=self.pool.get('product.product').browse(self.cr, self.uid, product_ids)        
        return product_proxy
