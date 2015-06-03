# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
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

from osv import osv, fields

class amazon_product_category_wizard(osv.osv_memory):    
    ''' Amazon parameter for migration linked to company
    '''    
    _name = 'amazon.product.category.wizard'

    # button event:
    def import_button(self, cr, uid, ids, context=None):
        ''' Button that import from destination DB the list of category to use 
            for Amazon product
        '''
        import xmlrpclib
        # Set up parameters (for connection to Open ERP Database) ********************************************
        dbname = "redesiderio" # TODO prelevare dalla configurazione Company
        user = "admin"
        pwd = "cgp.fmsp6"
        server = 'localhost'
        port = '8069'

        if not(dbname and user and pwd): # error
             raise osv.except_osv('Error!', 'Setup database access in Company form!')

        sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
        uid2 = sock.login(dbname, user, pwd)
        if not uid2:
             raise osv.except_osv('Error!', 'Bad login for user %s in destination DB: %s!'%(user, dbname))
            
        sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)        

        # TODO manage: amazon_mig_destination_code
        category_ids = sock.execute(dbname, uid2, pwd, 'amazon.product.category', 'search', [])
        
        category_pool=self.pool.get('amazon.product.category') 
        convert={}
        for category in sock.execute(dbname, uid2, pwd, 'amazon.product.category', 'read', category_ids):
            data= {'name': category['name'],
                   'code': category['code'],
                   'active': category['active'],
                   'destination_id': category['id'],
                   # no parent_id for now
                  }
            item_ids=category_pool.search(cr, uid, [('code','=',category['code'])], context=context)
            if item_ids: # update:            
                modify=category_pool.write (cr, uid, item_ids[0], data, context=context)
                convert[category['id']]=item_ids[0]
            else: #create
                create_id=category_pool.create (cr, uid, data, context=context)
                convert[category['id']]=create_id
                
        # Add parent_id now:        
        for category in sock.execute(dbname, uid2, pwd, 'amazon.product.category', 'read', category_ids):
            if category['parent_id'] and category['parent_id'][0] in convert:
                item_ids=category_pool.search(cr, uid, [('code','=',category['code'])], context=context)
                data= {'parent_id': convert[category['parent_id'][0]]}
                modify=category_pool.write (cr, uid, item_ids[0], data, context=context)
        return {'type':'ir.actions.act_window_close'}

    _columns = {
                'name':fields.char('Label', size=64, required=False, readonly=False),
                }
amazon_product_category_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
