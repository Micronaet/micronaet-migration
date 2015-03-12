# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#############################################################################
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
import sys
from osv import osv, fields
from tree import node


class migration_tools(osv.osv):
    ''' Tool for analysis pre migration
    '''
    _name = 'migration.tools'
    _description = 'Migration tools'
    
    def get_openerp_tree(self, cr, uid, context = None):
        ''' Generate a tree for every object
        '''
        tree_list = []
        import pdb; pdb.set_trace()
        for obj in self.pool.obj_pool:
            tree_list.append(node(
                                  openerp_obj = self.pool.obj_pool[obj], 
                                  openerp = self,
                                 )) # Create a tree form this element
            break # TODO remove 
        import pdb; pdb.set_trace()
        for t in tree_list:
            print "\nTable: %s %s" % (t.name, "*" * 20)
            t.show()
        import pdb; pdb.set_trace()    
        return True        
        
    _columns = {}
    
migration_tools() # 6.0 compliant
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
