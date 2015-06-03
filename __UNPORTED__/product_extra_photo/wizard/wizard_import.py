# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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

class product_extra_photo_wizard(osv.osv_memory):
    _name = 'product.extra.photo.wizard'
    _description = 'Import extra photo wizard'
    
    # Button function:
    def import_button(self, cr, uid, ids, context=None):
        """ Button for import images and link to product
        """
        
        result=self.pool.get("product.extra.photo").import_images(cr, uid, 0)
        return {'type' : 'ir.actions.act_window_close'}

    _columns = {
        'name':fields.char('Desription', size=64, required=True, readonly=False),
    }
    
    _defaults = {
        'name': lambda *a: "Import photo present in default location and parse name for link to product",
    }
product_extra_photo_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
