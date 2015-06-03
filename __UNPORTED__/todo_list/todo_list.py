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
import time

class res_partner_todo(osv.osv):
    _name = 'res.partner.todo'
    _description = 'Todo list'
    _order = 'complete,date,partner_id,name'
    
    def complete_todo(self, cr, uid, ids, context=None):
        ''' Button for tree view that permit to close activity        
        '''
        return self.write(cr, uid, ids, {'complete': True})
        
    _columns = {
        'name':fields.char('Short description', size=128, required=False, readonly=False),
        'complete':fields.boolean('Complete', required=False),        
        'date': fields.date('Date'),
        'deadline': fields.date('Deadline'),
        'note': fields.text('Note'),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }           
    
res_partner_todo()

class res_partner_extra_fields(osv.osv):
    """
        Add extra field to partner
    """
    
    _inherit = 'res.partner'

    def dummy_action_refresh(self, cr, uid, ids, context=None):
        return True

    _columns = {
        'todo_ids':fields.one2many('res.partner.todo', 'partner_id', 'Todo list', required=False),
    }
res_partner_extra_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
