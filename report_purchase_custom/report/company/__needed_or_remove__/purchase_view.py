# -*- encoding: utf-8 -*-
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

class product_product(osv.osv):
    _inherit = 'product.product'
    
    _columns = {
        'colls_number': fields.integer('Colli'), 
        'colls': fields.char('Colli', size=30), 
        }
    _defaults = {
        'colls_number': lambda *x: 1,
        }    
product_product()        
        
class purchase_order_extra(osv.osv):
    _inherit = 'purchase.order.line'
    
    _columns = {
        'q_x_pack': fields.related('product_id','q_x_pack', type='integer', string='Package'),        
        'colour': fields.related('product_id','colour', type='char', size=64, string='Color'),        
    }
purchase_order_extra()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
