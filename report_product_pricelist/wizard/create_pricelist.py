# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from tools.translate import _
from datetime import datetime

class micronaet_invoice_line(osv.osv):
    _name = 'micronaet.invoice.line'
    _description = 'Invoice line'
    _order = 'date'

    _columns = {
        'name':fields.char('Invoice number', size=10, required=True, readonly=False),
        'partner':fields.char('Invoice number', size=9, required=False, readonly=False),
        'price':fields.char('Invoice number', size=15, required=False, readonly=False),
        'quantity':fields.char('Invoice number', size=10, required=False, readonly=False),
        'product':fields.char('Invoice number', size=10, required=False, readonly=False),
        'date':fields.char('Invoice number', size=10, required=False, readonly=False),       
    }
micronaet_invoice_line()

# Product pricelist from model to generated:
class product_pricelist_generator(osv.osv_memory):
    """ Product pricelist generator 
        Copy an inactive pricelist creating a new pricelist with all product and
        calculate the price with actual pricelist rules
    """
    _name = "product.pricelist.generator"
    _description = "Product pricelist generator"

    _columns = {
        'pricelist_org_id':fields.many2one('product.pricelist', 'Original pricelist', required=True, help="Choose original pricelist used to calculate new complete pricelist/version"),
        'new':fields.boolean('New', required=False, help="Generate a new pricelist with this name"),
        'new_name': fields.char('New version name', size=64),
        'pricelist_des_id':fields.many2one('product.pricelist', 'Destination pricelist', required=False, help="If no new pricelist, use this pricelist to upgrade fields"),
    }

    _defaults = {
        'new': lambda *x: True,
    }

    '''def view_init(self, cr, uid, fields, context=None):
        idea_obj = self.pool.get('idea.idea')
        vote_obj = self.pool.get('idea.vote')

        for idea in idea_obj.browse(cr, uid, context.get('active_ids', []), context=context):

            for active_id in context.get('active_ids'):

                vote_ids = vote_obj.search(cr, uid, [('user_id', '=', uid), ('idea_id', '=', active_id)])
                vote_obj_id = vote_obj.browse(cr, uid, vote_ids)
                count = 0
                for vote in vote_obj_id:
                    count += 1

                user_limit = idea.vote_limit
                if  count >= user_limit:
                   raise osv.except_osv(_('Warning !'),_("You can not give Vote for this idea more than %s times") % (user_limit))

            if idea.state != 'open':
                raise osv.except_osv(_('Warning !'), _('Idea must be in "Open" state before vote for that idea.'))
        return False'''

    def do_create_update(self, cr, uid, ids, context=None):
        """
        Create or update pricelist
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of ids
        @return: Dictionary {}
        """
        
        if context is None:
           context={}
           
        wiz_browse = self.browse(cr, uid, ids[0], context=context)
        pricelist_ref_id = wiz_browse.pricelist_org_id.id
        if wiz_browse.new: # per ora facciamo questo
           if not wiz_browse.new_name: # TODO and duplicated!
              # TODO comunicate error!
              return {'type': 'ir.actions.act_window_close'}
              
           # Create new pricelist and pricelist version
           pricelist_id=self.pool.get('product.pricelist').create(cr, uid, {
                                                                            'name': wiz_browse.new_name, 
                                                                            'type': 'sale',
                                                                            'tipology': 'historical',
                                                                            # TODO currency 
                                                                           })
           if pricelist_id:
              version_id=self.pool.get('product.pricelist.version').create(cr, uid, {'name': "Versione: " + wiz_browse.new_name + " definitiva",
                                                                                     #'date_end': False, 
                                                                                     #'date_start': False, 
                                                                                     #'company_id': False, 
                                                                                     #'active': True, 
                                                                                     'pricelist_id': pricelist_id,
                                                                                    })
           else:
              pass # TODO comunicate error                                                                                 
        else:
           # Get pricelist and pricelist version            
           pricelist_id=0
           version_id=0
           
        if pricelist_id and version_id and wiz_browse.pricelist_org_id: # devono essere creati o trovati i listino/versione e deve esistere l'origine
           product_ids=self.pool.get('product.product').search(cr, uid, [('mexal_id', 'ilike', 'C')], context=context) # TODO write right filter
           for product in self.pool.get('product.product').read(cr, uid, product_ids, ['id', 'name', 'code',]):
               if product['code'][0:1].upper()=="C":
                  price_calc=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_ref_id], product['id'], 1.0, False, {'uom': False, 'date': False,})[pricelist_ref_id]
                               
                  self.pool.get('product.pricelist.item').create(cr, uid, {'price_round': 0.00001, 
                                                                        'price_discount': 0.0, #0.052600000000000001, 
                                                                        #'base_pricelist_id': False, 
                                                                        'sequence': 200, 
                                                                        'price_max_margin': 0.0, 
                                                                        #'company_id': False, 
                                                                        #'product_tmpl_id': False, 
                                                                        'product_id': product['id'], 
                                                                        'base': 1, 
                                                                        'price_version_id': version_id, #[3, 'Rif. anno 2011'], 
                                                                        'min_quantity': 1, 
                                                                        'price_surcharge': price_calc,  # TODO Calcolare in funzione del listino
                                                                        #'price_min_margin': 0.0, 
                                                                        #'categ_id': False,
                                                                        'name': "[%s] %s"%(product['code'], product['name']),
                                                                        })
        else:
           pass # TODO comunicate error!
        return {'type': 'ir.actions.act_window_close'}
            
product_pricelist_generator()

# Product pricelist for customer:
class product_pricelist_customer(osv.osv_memory):
    """ Product pricelist generator for customers
    """
    _name = "product.pricelist.customer"
    _description = "Product pricelist customer"

    _columns = {
        'partner_id':fields.many2one('res.partner', 'Partner', required=True, help="Choose partner to create custom pricelist or add quotations"),
        'comment': fields.char('Comment', size=64, help="Need to be created or updated"),        
        'product_id': fields.many2one('product.product', 'Product', required=True),

        'pricelist_id':fields.many2one('product.pricelist', 'Current pricelist', required=True, help="Choose original pricelist used to calculate new complete pricelist/version"),
        'pricelist_model_history_id':fields.many2one('product.pricelist', 'Listino di riferimento', help="Listino di riferimento applicato nel caso mancassero degli articoli nel listino di base (usato per avere un raffronto nel caso esistessero particolarità"),
        'pricelist_model_id':fields.many2one('product.pricelist', 'Listino di paragone', help="Listino di paragone per avere un raffronto con il prezzo attuale del prodotto"),


        'price': fields.float('Price listino cliente', digits=(16, 5)),
        'price_model_history': fields.float('Prezzo list di rif.', digits=(16, 5)),
        'price_model': fields.float('Prezzo di paragone', digits=(16, 5)),
        'price_history': fields.text('Prezzo storico'),

        'price_invoice_history': fields.text('Prezzo storico fatturato'),
    }

    # on change function
    def onchange_pricelist(self, cr, uid, ids, pricelist_id, product_id, context = None):
        ''' Read price from pricelist for product
        '''
        if context is None:
           context={}
        
        res={'value':{}}
        if pricelist_id: # cerco il listino
           res['value']['price']=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], product_id , 1.0, False, {'uom': False, 'date': False,})[pricelist_id]
           return res # fino a qui per ora
        #Azzero il prezzo
        return {'value': {'price': False,}}

    def onchange_partner_pricelist(self, cr, uid, ids, partner_id, pricelist_id, product_id, context = None):
        '''Create a new pricelist if not custom
           add custom price
           add old version as reference
        '''
        if context is None:
           context={}
        
        res={'value':{}}
        if partner_id: # cerco il listino
           partner=self.pool.get("res.partner").browse(cr, uid, partner_id)
           partner_pricelist_id = partner.property_product_pricelist.id or 0

           if not pricelist_id: # pricelist_id only if not passed (to keep the change)
              pricelist_id=partner_pricelist_id 
           
           res['value']['pricelist_id']=pricelist_id
           res['value']['pricelist_model_history_id']=partner.pricelist_model_history_id.id or 0
           res['value']['pricelist_model_id']=partner.pricelist_model_id.id or 0
           return res # fino a qui per ora

        return {'value': {}}
              
    def onchange_partner_pricelist_product(self, cr, uid, ids, partner_id, pricelist_id, product_id, pricelist_model_history_id, pricelist_model_id, context = None):
        '''Create a new pricelist if not custom
           add custom price
           add old version as reference
        '''
        if context is None:
           context={}
        
        res={'value':{}}
        if product_id and pricelist_id: # cerco il listino
           #import pdb; pdb.set_trace()
           res['value']['price']=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], product_id , 1.0, False, {'uom': False, 'date': False,})[pricelist_id] if pricelist_id else ""
           res['value']['price_model_history']=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_model_history_id], product_id , 1.0, False, {'uom': False, 'date': False,})[pricelist_model_history_id] if pricelist_model_history_id else ""
           res['value']['price_model']=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_model_id], product_id , 1.0, False, {'uom': False, 'date': False,})[pricelist_model_id] if pricelist_model_id else ""
           
           # Order history:
           order_line_ids=self.pool.get('sale.order.line').search(cr, uid, [('product_id','=',product_id),('order_partner_id','=',partner_id)]) 
           if order_line_ids:
              list_quotation="%20s%20s%20s%40s\n"%("Data","Ordine","Prezzo", "Commento")            

              for line in self.pool.get('sale.order.line').browse(cr, uid, order_line_ids):
                  list_quotation+="%20s%20s%20s%40s\n"%(datetime.strptime(line.order_id.date_order, '%Y-%m-%d').strftime('%d/%m/%Y'), line.order_id.name, line.price_unit, line.price_comment or "")
              res['value']['price_history']=list_quotation
           else:
              res['value']['price_history']=""

           # Invoice history:
           #import pdb; pdb.set_trace()
           product_proxy=self.pool.get('product.product').browse(cr, uid, product_id)
           product_code=product_proxy.code #"C3114409"
           partner_proxy=self.pool.get('res.partner').browse(cr, uid, partner_id)
           partner_code=partner_proxy.mexal_c #"230.00179" # TODO parametrizzare
           invoice_line_ids=self.pool.get('micronaet.invoice.line').search(cr, uid, [('product','=',product_code),('partner','=',partner_code)]) 
           if invoice_line_ids:
              list_quotation="%20s%20s%20s%20s\n"%("Data","Fattura","Prezzo", "Q.")            

              for line in self.pool.get('micronaet.invoice.line').browse(cr, uid, invoice_line_ids):
                  list_quotation+="%20s%20s%20s%20s\n"%(datetime.strptime(line.date, '%Y%m%d').strftime('%d/%m/%Y'), line.name, line.price, line.quantity)
              res['value']['price_invoice_history']=list_quotation
           else:
              res['value']['price_invoice_history']=""

           return res 
           
        # Azzero tutto:   
        return {'value': {'price':False,
                          'price_model_history':False,
                          'price_model':False,
                          'price_history':False,                          
                          'price_invoice_history':False,                          
                          }}

    # event function
    def do_insert_quotation(self, cr, uid, ids, context=None):
       """
       Create or update pricelist if non custom and add personalization
       @param cr: the current row, from the database cursor,
       @param uid: the current user’s ID for security checks,
       @param ids: List of ids
       @return: Dictionary {}
       """
       
       if context is None:
          context={}

       wiz_browse = self.browse(cr, uid, ids[0], context=context)        
       customer_proxy=self.pool.get('res.partner').browse(cr, uid, wiz_browse.partner_id.id) 
       pricelist_org_id = wiz_browse.pricelist_id.id # old pricelist set up
       pricelist_proxy=self.pool.get('product.pricelist').browse(cr, uid, pricelist_org_id)
        
       if not pricelist_proxy.customized: # Create customized and first rule
          update=False
          pricelist_ref_id=self.pool.get('product.pricelist').create(cr, uid, {
                                                                                'name': "Personal: " + customer_proxy.name, 
                                                                                'type': 'sale',
                                                                                'customized': True,
                                                                                # TODO currency 
                                                                               })
          if pricelist_ref_id:
              version_ref_id=self.pool.get('product.pricelist.version').create(cr, uid, {'name': "From " + customer_proxy.property_product_pricelist.name,
                                                                                         #'date_end': False, 
                                                                                         #'date_start': False, 
                                                                                         #'company_id': False, 
                                                                                         #'active': True, 
                                                                                         'pricelist_id': pricelist_ref_id, #appena creato
                                                                                         })
          else:
              pass # TODO comunicate error                                                                                 
                                                                           
       else: # yet custom pricelist
          update=True
          pricelist_ref_id = customer_proxy.property_product_pricelist.id           
          version_ref_id = customer_proxy.property_product_pricelist.version_id[0].id # TODO take the first for now!
           
       if not (pricelist_ref_id and version_ref_id):
          # TODO comunicate error!
          return {'type': 'ir.actions.act_window_close'}
           
       pricelist_item_pool = self.pool.get('product.pricelist.item')
       # Creo l'ultima regola per prendere come riferimento il listino precedente
       if not update: # Create ref. pricelist only for first new!
          rule_id = pricelist_item_pool.create(cr, uid, {'price_round': 0.00001, 
                                            'price_discount': 0.0, #0.052600000000000001, 
                                            'sequence': 500,  # ultima
                                            'price_max_margin': 0.0, 
                                            'base': 2,  # pricelist version
                                            'price_version_id': version_ref_id, #owner version
                                            'min_quantity': 1, 
                                            'price_surcharge': 0.0, 
                                            'base_pricelist_id': pricelist_ref_id,
                                            'name': "Listino rif: " + customer_proxy.property_product_pricelist.name,
                                            })
       # Creo la regola in base a prezzo e prodotto attuale
       # TODO cercare se esiste già!!!!!
       rule_id = pricelist_item_pool.create(cr, uid, {'price_round': 0.00001, 
                                            'price_discount': 0.0, #0.052600000000000001, 
                                            'sequence': 10, # tra le prime
                                            'price_max_margin': 0.0, 
                                            'product_id': wiz_browse.product_id.id, 
                                            'base': 1,
                                            'price_version_id': version_ref_id,
                                            'min_quantity': 1, 
                                            'price_surcharge': wiz_browse.price,
                                            'name': "[%s] %s"%(wiz_browse.product_id.code, wiz_browse.product_id.name),
                                            })
       # Set up partner with new pricelist                                     
       self.pool.get('res.partner').write(cr, uid, [wiz_browse.partner_id.id], {'property_product_pricelist': pricelist_ref_id,})
       #price_calc=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_ref_id], product['id'], 1.0, False, {'uom': False, 'date': False,})[pricelist_ref_id]
       return {'type': 'ir.actions.act_window_close'}
            
product_pricelist_customer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
