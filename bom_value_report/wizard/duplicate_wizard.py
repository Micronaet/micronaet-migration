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
import pdb

class duplicate_bom_wizard(osv.osv_memory):
    '''Wizard for duplicate BOM from a product to another (create BOM if not
       present. Remove all component if present.
    ''' 
    _name = 'duplicate.bom.wizard'

    def return_view(self, cr, uid, name, res_id):
        '''Function that return dict action for next step of the wizard'''
        return {
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'mrp.bom', # object linked to the view
                #'views': [(view_id, 'form')],
                'view_id': False,
                'type': 'ir.actions.act_window',
                #'target': 'new',
                'res_id': res_id,  # ID selected
               }

    _columns = {
                'clear': fields.boolean('Cancella componenti', help='Elimina tutti gli eventuali componenti presenti nella Distinta selezionata.', required=False),
                'duplicate_to':fields.many2one('mrp.bom', 'Duplica su', required=False),
                'create_duplicate_to':fields.many2one('product.product', 'Crea distinta prodotto', required=False),
               }

    _defaults={
              'clear': lambda *a: True, 
              }

    def duplicate_bom(self,cr, uid, ids, context=None):
        '''Duplicate function launched by the wizard'''
        
        if context is None:
           context = {}

        from_id = context.get("active_id",0) # get from ID 
        
        if not from_id: # not present from ID
           raise osv.except_osv("Errore", "Non trovato l'elemento da cui partire!")
           
        else: # try to duplicate
           wiz_proxy = self.browse(cr, uid, ids, context) # search wizard element 
           
           bom_pool = self.pool.get("mrp.bom") # get the pool to copy element
           product_pool = self.pool.get("product.product") # get the pool to get info from product

           # Beginning test of coerence:         
           if not wiz_proxy: # There's no wizard element
              raise osv.except_osv("Errore", "Errore caricando i dati dal wizard")
           if wiz_proxy[0].duplicate_to and wiz_proxy[0].create_duplicate_to: # both data are insert 
              raise osv.except_osv("Errore", "Inserire la distina o il prodotto non entrambi!")
           if not wiz_proxy[0].duplicate_to and not wiz_proxy[0].create_duplicate_to: # both data are insert 
              raise osv.except_osv("Errore", "Inserire la distina o il prodotto!")
              
           if wiz_proxy[0].create_duplicate_to: # Create BOM of product selected (if not exist)
              bom_ids = bom_pool.search(cr, uid, [
                  ('product_id', '=', wiz_proxy[0].create_duplicate_to.id),('bom_id', '=', False)])
              if bom_ids: # already exist BOM
                 to_bom_id = bom_ids[0] # take the first
              else: # create bom
                 product_proxy = product_pool.browse(
                     cr, uid, wiz_proxy[0].create_duplicate_to.id)
                 to_bom_id = bom_pool.create(cr, uid, {
                     'name': product_proxy.name,
                     'code': product_proxy.code,
                     'product_id': product_proxy.id,
                     'product_qty': 1,
                     'product_uos': product_proxy.uos_id.id or False,
                     'product_uom': product_proxy.uom_id.id or False, 
                     })                 
           else: # Duplication in BOM selected
               to_bom_id= wiz_proxy[0].duplicate_to.id
           
           # Check if existing elements must be deleted:
           if wiz_proxy[0].clear:
              bom_ids_to_delete = bom_pool.search(cr, uid, [
                  ('bom_id', '=', to_bom_id)])
              deleted = bom_pool.unlink(cr, uid, bom_ids_to_delete) # remove element with father bom_id
           
           # Create element with duplication:
           bom_lines = bom_pool.browse(cr, uid, from_id).bom_lines # read all components
           for component in bom_lines: # loop for duplication
               bom_component_data = {
                   #'product_uos_qty': component.product_uos_qty, 
                   'code': component.code, 
                   'product_uom': component.product_uom and component.product_uom.id, 
                   'obsolete': component.obsolete, 
                   'product_qty': component.product_qty, 
                   'product_uos': component.product_uos.id, 
                   'date_start': component.date_start, 
                   'company_id': component.company_id and component.company_id.id, 
                   'type': component.type, 
                   'method': component.method, 
                   'bom_id': to_bom_id,
                   'active': component.active, 
                   'name': component.name, 
                   'product_id': component.product_id and component.product_id.id,
                   'position': component.position
                   }
               created_id = bom_pool.create(
                   cr, uid, bom_component_data) # copy with replace of
           
        return self.return_view(cr, uid, 'mrp_bom_form', to_bom_id) # call view with new id
duplicate_bom_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

