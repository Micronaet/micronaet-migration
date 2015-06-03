# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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

from osv import fields,osv
import time

class res_partner_todo_generate_wizard(osv.osv_memory):
    """Generate a list of res.partner.todo from a note fields
       every line is an activity
    """
    _name = 'res.partner.todo.wizard'
    
    _columns = {
                'date': fields.date('Date'),
                'deadline': fields.date('Deadline'),
                'note': fields.text('Note', required=True),
                'partner_id':fields.many2one('res.partner', 'Partner', required=False),
               }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }           
    
    def return_view(self, cr, uid, name, res_id):
        '''Function that return dict action for next step of the wizard'''
        return {
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'res.partner', 
                #'views': [(view_id, 'form')],
                'view_id': False,
                'type': 'ir.actions.act_window',
                #'target': 'new',
                'res_id': res_id,  # ID selected
               }

    
    def action_convert_note_todo(self, cr, uid, ids, context=None):
        """
        The cancel action for workflow
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids on which business flow executes
        @param *args: other arguments 
       
        @return: return True if all constraints satisfied, False otherwise
        """
        if context is None:
           context={}
           
        #import pdb; pdb.set_trace()   
        wiz_browse=self.browse(cr, uid, ids[0], context=context)
        
        for todo_item in wiz_browse.note.split("\n"):
            if todo_item:
               todo_item_id=self.pool.get('res.partner.todo').create(cr, uid, { 'complete': False,
                                                                                'date': wiz_browse.date,
                                                                                'deadline': wiz_browse.date,
                                                                                'name': todo_item,
                                                                                'partner_id': wiz_browse.partner_id.id, 
                                                                                'note': '',
                                                                      })
        return True #{ 'type' : 'ir.actions.act_window.close' }

    '''def action_close_todo(self, cr, uid, ids, context=None):
        wiz_browse=self.browse(cr, uid, ids[0], context=context)
        return self.return_view(cr, uid, 'res.partner', wiz_browse.partner_id.id) '''

res_partner_todo_generate_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

