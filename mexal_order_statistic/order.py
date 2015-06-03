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


class statistic_invoice_agent(osv.osv):
    _name = 'statistic.invoice.agent'
    _description = 'Invoice Agent'
    _columns = {
        'name':fields.char('Agent', size=64, required=True, readonly=False),
        'ref':fields.char('Code', size=10, required=False),
        'hide_statistic': fields.boolean('Nascondi statistica'),
        #'trend': fields.boolean('Trend', required=False),
    }    
    _defaults = {
        #'trend': lambda *a: False,
    }
statistic_invoice_agent()

class statistic_category(osv.osv):
    _name = 'statistic.category'
    _description = 'Categoria statistica'
    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'trend':fields.boolean('Trend', required=False),
    }    
    _defaults = {
        'trend': lambda *a: False,
    }
statistic_category()

class res_partner_extra_fields(osv.osv):
    """
    res_partner_extra_fields
    """
    
    _inherit = 'res.partner'
    _name = 'res.partner'
    
    _columns = {
        'invoice_agent_id':fields.many2one('statistic.invoice.agent', 'Invoice Agent', required=False),
        #'hide_statistic': fields.related(
        #    'invoice_agent_id',
        #    'hide_statistic', 
        #    type='boolean', 
        #    string='Nascondi statistica'),         
        'trend': fields.boolean('Trend', help='Insert in trend statistic, used for get only interesting partner in statistic graph',required=False),

        'open_payment_ids':fields.one2many('statistic.deadline', 'partner_id', 'Pagamenti aperti', required=False),
        'statistic_category_id':fields.many2one('statistic.category', 'Categoria statistica', help='Valore di categoria statistica acquisito dal gestionale', required=False),
        'trend_category': fields.related('statistic_category_id','trend', type='boolean', string='Categoria trend', help='Indica se la gategoria viene rappresentata nel grafico del trend', readonly=True),

        'saldo_c': fields.float('Saldo cliente', digits=(16, 2)),
        'saldo_s': fields.float('Saldo fornitore', digits=(16, 2)),

        'ddt_e_oc_c': fields.float('Saldo cliente OC+DDT aperti', digits=(16, 2)),
        'ddt_e_oc_s': fields.float('Saldo fornitore OC+DDT aperti', digits=(16, 2)),
    }
res_partner_extra_fields()

class statistic_header(osv.osv):
    _name = 'statistic.header'
statistic_header()

class statistic_order(osv.osv):
    '''Object that contain all order header coming from accounting
       This is only for statistic view or graph
    '''
    _name = 'statistic.order'
    _description = 'Statistic order'
    
    _order='sequence'

    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'visible':fields.boolean('Visible',),
        'sequence': fields.integer('Sequence'),
        #'calendar_description': fields.function(_function_calculate_lines_details, method=True, type='char', size=100, string='Total lines', store=False,),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'property_account_position': fields.related('partner_id', 'property_account_position', type='many2one', relation='account.fiscal.position', store=True, string='Fiscal position'),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)),
        'country_id': fields.related('partner_id', 'country', type='many2one', relation='res.country', string='Country', store=True),
        'zone_id': fields.related('partner_id', 'zone_id', type='many2one', relation='res.partner.zone', string='Zona', store=True),
        # Parte delle righe dettaglio:
        'code':fields.char('Code', size=24, required=False, readonly=False),
        'article':fields.char('Article', size=64, required=False, readonly=False),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'colli': fields.integer('Colli'),
        'quantity_ok': fields.float('Prodotti', digits=(16, 2)),
        'type': fields.selection([('b','Prodotto'),('n','Annullato'),],'Type of line'),
        'line_type': fields.selection([('a','Articolo'),('d','Descrizione'),],'Line type'),
        # Parte calcolata da visualizzare per prodotto:
        'total_linear_meter': fields.float('Total m/l', digits=(16, 2)),
        'total_volume': fields.float('Total volume', digits=(16, 2)),
        'total_weight': fields.float('Total weight', digits=(16, 2)),
        'note':fields.char('Note', size=64, required=False, readonly=False),

        'header_id':fields.many2one('statistic.header', 'Dettagli', required=False),        
        }
statistic_order()

class statistic_header_inherit(osv.osv):
    _name = 'statistic.header'
    _inherit = 'statistic.header'

    _order='deadline, name'
    _description = 'Testate ordini'

    def to_print(self, cr, uid, ids, context = None):
        # import pdb; pdb.set_trace()
        header_mod=self.write(cr, uid, ids, {'print': True}, context=context)                
        return True

    def no_print(self, cr, uid, ids, context = None):
        # import pdb; pdb.set_trace()
        header_mod=self.write(cr, uid, ids, {'print': False}, context=context)                
        return True
        
    def _function_order_header_statistic(self, cr, uid, ids, field_name, arg, context = None):
        """ Calcola i campi statistici nell'ordine
        """
        if context is None:
           context={}
           
        res={}   
        for header in self.browse(cr, uid, ids, context=context):                               
            res[header.id]={}
            res[header.id]['complete'] = True # initial value
            res[header.id]['total_item'] = 0.0
            res[header.id]['total_item_complete'] = 0.0
            res[header.id]['total_linear_meter'] = 0.0
            res[header.id]['total_linear_meter_ready'] = 0.0
            res[header.id]['total_volume'] = 0.0
            res[header.id]['total_volume_ready'] = 0.0
            res[header.id]['total_weight'] = 0.0
            for line in header.line_ids:
                res[header.id]['total_item'] += line.quantity or 0.0
                res[header.id]['total_item_complete'] += line.quantity_ok or 0.0
                res[header.id]['total_linear_meter'] += line.total_linear_meter or 0.0
                res[header.id]['total_volume'] += line.total_volume or 0.0
                res[header.id]['total_weight'] += line.total_weight or 0.0
                
                if line.line_type=='a' and not line.type=='b': # test only A(rticle) line
                    res[header.id]['complete'] = False
                    
                if line.type=='b':
                   res[header.id]['total_linear_meter_ready'] += line.total_linear_meter or 0.0
                   res[header.id]['total_volume_ready'] += line.total_volume or 0.0
                # vedere per volume e metrature                
        return res
    
    
    _columns = {
        'name':fields.char('Numero ordine', size=16, required=False, readonly=False),
        'visible':fields.boolean('Visible',),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'date': fields.date('Date'),
        'deadline': fields.date('Scadenza'),
        'total': fields.float('Total', digits=(16, 2)), # TODO calcolato
        'note': fields.char('Note', size=64, required=False, readonly=False),        
        'print':fields.boolean('To print', required=False),

        'registration_date': fields.date('Registration date'),
        'extra_note': fields.char('Extra Note', size=64, required=False, readonly=False),

        'agent_description': fields.char('Agent description', size=36, required=False, readonly=False),        
        
        'property_account_position': fields.related('partner_id', 'property_account_position', type='many2one', relation='account.fiscal.position', store=True, string='Fiscal position'),
        'country_id': fields.related('partner_id', 'country', type='many2one', relation='res.country', string='Country', store=True),
        'zone_id': fields.related('partner_id', 'zone_id', type='many2one', relation='res.partner.zone', string='Zona', store=True),
        
        'line_ids':fields.one2many('statistic.order', 'header_id', 'Linee dettaglio', required=False),

        # Campi funzione:
        'complete': fields.function(_function_order_header_statistic, method=True, type='boolean', string='Completo', multi="statistiche", store=False),
        'total_item': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='N. art.', multi="statistiche", store=False),
        'total_item_complete': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='N. Art. (pronti)', multi="statistiche", store=False),
        'total_linear_meter': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='Mt. lineari', multi="statistiche", store=False),
        'total_linear_meter_ready': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='Mt. lineari (pronti)', multi="statistiche", store=False),
        'total_volume': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='Volume', multi="statistiche", store=False),
        'total_volume_ready': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='Volume (pronto)', multi="statistiche", store=False),
        'total_weight': fields.function(_function_order_header_statistic, method=True, type='float', digits=(16, 2), string='Peso', multi="statistiche", store=False),

        'port_code': fields.selection([('f','Franco'),('a','Assegnato'),('d','Addebito'),],'Port'),
        'port_description':fields.char('Port description', size=40, required=False, readonly=False),
        'destination':fields.char('Destination ', size=40, required=False, readonly=False),
        'destination_address':fields.char('Destination address ', size=40, required=False, readonly=False),
        'destination_cap':fields.char('Destination cap', size=40, required=False, readonly=False),
        'destination_country':fields.char('destination country', size=40, required=False, readonly=False),
        'destination_prov':fields.char('destination province', size=40, required=False, readonly=False),
    }
statistic_header_inherit()


class statistic_deadline(osv.osv):
    _name = 'statistic.deadline'
    _description = 'Statistic deadline'
    _order='name,deadline' # name is loaded with partner name during import
    
    _columns = {
        'name':fields.char('Deadline', size=64, required=False, readonly=False),
        'visible':fields.boolean('Visible',),

        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'property_account_position': fields.related('partner_id', 'property_account_position', type='many2one', relation='account.fiscal.position', store=True, string='Fiscal position'),
        'c_o_s':fields.char('Cl. o For.', size=1, required=False, readonly=False),
        'deadline': fields.date('Dead line'),
        #'deadline_real': fields.date('Dead line'),
        #'actualized':fields.boolean('Scadenza attualizzata', required=False),

        'fido_date': fields.related('partner_id', 'fido_date', type="date", string="Data fido",),
        'fido_ko':fields.related('partner_id', 'fido_ko', type="boolean", string="Fido concesso",),
        'fido_total': fields.related('partner_id', 'fido_total',  type="float", digits=(16, 2), string="Importo fido",),
        
        'total': fields.float('Total', digits=(16, 2)),
        'in': fields.float('Entrate', digits=(16, 2)),
        'out': fields.float('Uscite', digits=(16, 2)),

        # Non fatto related ma calcolato al volo
        'scoperto_c':  fields.float('Scoperto cliente', digits=(16, 2)),
        'scoperto_s':  fields.float('Scoperto fornitore', digits=(16, 2)),

        'saldo_c': fields.related('partner_id', 'saldo_c', type='float', digits=(16, 2), string='Saldo (cliente)',),
        'saldo_s': fields.related('partner_id', 'saldo_s', type='float', digits=(16, 2), string='Saldo (fornitore)',),

        'ddt_e_oc_c': fields.related('partner_id', 'ddt_e_oc_c', type='float', digits=(16, 2), string='DDT + OC aperti (cliente)',),
        'ddt_e_oc_s': fields.related('partner_id', 'ddt_e_oc_s', type='float', digits=(16, 2), string='DDT + OC aperti (fornitore)',),

        'type':fields.selection([
            ('b','Bonifico'),            
            ('c','Contanti'),            
            ('r','RIBA'),            
            ('t','Tratta'),            
            ('m','Rimessa diretta'),            
            ('x','Rimessa diretta X'),
            ('y','Rimessa diretta Y'),            
            ('z','Rimessa diretta Z'),            
            ('v','MAV'),            
        ],'Type', select=True, readonly=False),   
    }
    _defaults = {
        'total': lambda *a: 0,
        'in': lambda *a: 0,
        'out': lambda *a: 0,
        'scoperto_c': lambda *a: 0,
        'scoperto_s': lambda *a: 0,
    }
statistic_deadline()

class statistic_trend(osv.osv):
    _name = 'statistic.trend'
    _description = 'Statistic Trend'
    
    def _function_index_increment(self, cr, uid, ids, field_name=None, arg=False, context=None):
        """
        Calcola il migliore e il peggiore incremento rispetto l'anno precedente
        """
        if context is None:
           context = {}
           
        result = {}
        for item in self.browse(cr, uid, ids, context=context):
            result[item.id]={}
            increment=(item.total or 0.0) - (item.total_last or 0.0)
            if increment > 0: #increment (best)
               result[item.id]['best']=increment or 0.0
               result[item.id]['worst']= 0.0
            else: # decrement (worst)    
               result[item.id]['worst']=-increment or 0.0
               result[item.id]['best']= 0.0
        return result
            
    _columns = {
        'name':fields.char('Description', size=64, required=False, readonly=False),
        'visible':fields.boolean('Visible',),
        
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),

        'percentage': fields.float('% sul fatt. attuale', digits=(16, 5)),
        'percentage_last': fields.float('% sul fatt. stag. -1', digits=(16, 5)),
        'percentage_last_last': fields.float('% sul fatt. stag. -2', digits=(16, 5)),

        'total': fields.float('Tot. stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Tot. stag. -1', digits=(16, 2)),        
        'total_last_last': fields.float('Tot. stag. -2', digits=(16, 2)),        

        'trend_category': fields.related('partner_id', 'trend_category', type='boolean', readonly=True, string='Categoria trend'),
        'statistic_category_id': fields.related('partner_id', 'statistic_category_id', type='many2one', relation="statistic.category", readonly=True, string='Categoria statistica partner'),
        'trend': fields.related('partner_id', 'trend', type='boolean', readonly=True, string='Important partner'),

        'type_document':fields.selection([('ft','Fattura'),
                                          ('oc','Ordine'),
                                          ('bc','DDT'),
                                         ],'Tipo doc.', select=True),

        'best': fields.function(_function_index_increment, method=True, type='float', string='Best trend', multi='indici', store=True,),
        'worst': fields.function(_function_index_increment, method=True, type='float', string='Worst trend', multi='indici', store=True,),
    }
statistic_trend()

class statistic_trendoc(osv.osv):
    '''Creato stesso oggetto che conterrà pero il fatturato e gli ordini in 
       scadenza per il mese
    '''
    _inherit = 'statistic.trend'
    _name = 'statistic.trendoc'
statistic_trendoc()

class statistic_invoice(osv.osv):
    _name = 'statistic.invoice'
    _description = 'Statistic invoice'
    _order = 'month, name'
    
    _columns = {
        'name':fields.char('Descrizione', size=64, required=False, readonly=False),
        'visible':fields.boolean('Visible',),        
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'invoice_agent_id': fields.related('partner_id','invoice_agent_id', 
            type='many2one', relation='statistic.invoice.agent', 
            string='Invoice agent'),
        'hide_statistic':  fields.related('invoice_agent_id','hide_statistic', 
            type='boolean', string='Nascondi statistica'),
        'type_cei': fields.related('partner_id','type_cei', type='char', 
            size=1, string='C E I'),
        'total': fields.float('Stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Stag. -1', digits=(16, 2)),        
        'total_last_last': fields.float('Stag. -2', digits=(16, 2)),        
        'total_last_last_last': fields.float('Stag. -3', digits=(16, 2)),        
        'total_last_last_last_last': fields.float('Stag. -4', digits=(16, 2)),
        'season_total': fields.char('Totale', size=15, help='Only a field for group in graph total invoice'),
        'type_document':fields.selection([
            ('ft', 'Fattura'),
            ('oc', 'Ordine'),
            ('bc', 'DDT'),
            ], 'Tipo doc.', select=True),
        'month':fields.selection([
            (0, '00 Non trovato'),
            (1, 'Mese 05*: Gennaio'),
            (2, 'Mese 06*: Febbraio'),
            (3, 'Mese 07*: Marzo'),
            (4, 'Mese 08*: Aprile'),
            (5, 'Mese 09*: Maggio'),
            (6, 'Mese 10*: Giugno'),
            (7, 'Mese 11*: Luglio'),
            (8, 'Mese 12*: Agosto'),
            (9, 'Mese 01: Settembre'),
            (10, 'Mese 02: Ottobre'),
            (11, 'Mese 03: Novembre'),            
            (12, 'Mese 04: Dicembre'),            
            ],'Mese', select=True, readonly=False),  
        'trend': fields.related('partner_id', 'trend', type='boolean', 
            readonly=True, string='Important partner'),

        # Extra info for filter graph:
        'zone_id': fields.related('partner_id','zone_id', type='many2one', 
            relation='res.partner.zone', string='Zone', store=True),
        'zone_type': fields.related('zone_id','type', type='selection', 
            selection=[
                ('region', 'Region'), ('state', 'State'), ('area', 'Area'),
                ], string='Tipo', store=True),
        'country_id': fields.related('partner_id','country', type='many2one', 
            relation='res.country', string='Country', store=True),
    }
    
    _defaults = {
        'total': lambda *a: 0.0,
        'total_last': lambda *a: 0.0,
        'total_last_last': lambda *a: 0.0,
        'total_last_last_last': lambda *a: 0.0,
        'total_last_last_last_last': lambda *a: 0.0,
        'season_total': lambda *a: 'Totale', # always the same
        'visible': lambda *a: False,
    }
statistic_invoice()

class statistic_invoice_product(osv.osv):
    _name = 'statistic.invoice.product'
    _description = 'Statistic invoice'
    _order = 'month, name'
    
    _columns = {
        'name':fields.char('Famiglia prodotto', size=64, required=False, readonly=False),        
        'visible':fields.boolean('Visible',), ## used!
        'total': fields.float('Stag. attuale', digits=(16, 2)),
        'total_last': fields.float('Stag. -1', digits=(16, 2)),        
        'total_last_last': fields.float('Stag. -2', digits=(16, 2)),        

        'percentage': fields.float('% sul fatt. stag. corrente', digits=(16, 5)),
        'percentage_last': fields.float('% sul fatt. stag. -1', digits=(16, 5)),
        'percentage_last_last': fields.float('% sul fatt. stag. -2', digits=(16, 5)),

        'type_document':fields.selection([('ft','Fattura'),   
                                          ('oc','Ordine'),
                                          ('bc','DDT'),
                                         ],'Tipo doc.', select=True), # togliere?
        'month':fields.selection([
            (0,'00 Non trovato'),
            (1,'Mese 05*: Gennaio'),
            (2,'Mese 06*: Febbraio'),
            (3,'Mese 07*: Marzo'),
            (4,'Mese 08*: Aprile'),
            (5,'Mese 09*: Maggio'),
            (6,'Mese 10*: Giugno'),
            (7,'Mese 11*: Luglio'),
            (8,'Mese 12*: Agosto'),
            (9,'Mese 01: Settembre'),
            (10,'Mese 02: Ottobre'),
            (11,'Mese 03: Novembre'),            
            (12,'Mese 04: Dicembre'),            
        ],'Mese', select=True, readonly=False),  
    }
    _defaults = {
        'total': lambda *a: 0.0,
        'total_last': lambda *a: 0.0,
        'total_last_last': lambda *a: 0.0,
        'visible': lambda *a: False,
    }
statistic_invoice_product()

class statistic_invoice_product_removed(osv.osv):
    ''' Product not present in statistic
    '''
    _name = 'statistic.invoice.product.removed'
    _description = 'Statistic Product to remove'
    _columns = {
        'name':fields.char('Famiglia', size = 64, required = True, readonly = False),
    }    
statistic_invoice_product_removed()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
