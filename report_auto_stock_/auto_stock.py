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
import sys

class auto_stock_supplier(osv.osv):
    _name = 'auto.stock.supplier'
    _description = 'Supplier list'
    _order = 'name'
    
    def export_product_supplier_list(self, cr, uid, file_name = '/tmp/prodotti.csv', context=None):
        ''' Procedura di esportazione lista prodotti con prezzi e descrizioni
            fornitore, e' fatta per essere chiamata via XMLRPC
        '''        
        from_text= {u'ø': ' diam. ',
                    u'%': ' perc. ',
                    u'Ø': ' diam. ',
                    u'à': 'a\'',
                    u'ò': 'o\'',
                    u'è': 'e\'',
                    u'é': 'e\'',
                    u'è': 'e\'',
                    u'+':' piu\'',
                   }

        def translate(text):
            ''' Translate not ascii char
            '''
            try:
                return ''.join(c for c in text if ord(c) < 128)
            except:    
                import pdb; pdb.set_trace()
        
        def write_line(file_csv, data):
            ''' Write the csv data:                
            '''
            file_csv.write("%(product_name)s;\'%(product_code)s;%(supplier)s;%(supplier_name)s;\'%(supplier_code)s;'%(min_qty)s;'%(delay)s;'%(price)s;'%(min_quantity)s;%(quotation_date)s;\r\n"%(data))
            return 
            
        if context is None:
            context = {}
            
        context['lang']='it_IT'
        
        try:
            product_pool = self.pool.get('product.product')
            product_ids = product_pool.search(cr, uid, [], context=context)
            file_csv = open(file_name, "w")

            fields_header = [
                'Prodotto Fiam', 'Codice Fiam', 'Fornitore',
                'Prodotto Fornitore', 'Codice Fornitore', 'Min. Q.', 
                'Tempi di cons.', 'Prezzo', 'Lotto', 'Data quotazione',
                'Q. ordine']
            fields = (
                'product_name', 'product_code', 'supplier', 
                'supplier_name', 'supplier_code', 'min_qty', 
                'delay', 'price', 'min_quantity', 'quotation_date')
                
            # Write header line:    
            file_csv.write(("%s\r\n" % (
                fields_header)).replace("[","").replace("]","").replace(",",";").replace("'",""))
                
            for product in product_pool.browse(cr, uid, product_ids, context=context):
                data = {}.fromkeys(fields, "") # empty DB
                try:
                    data['product_name'] = translate(product.name) if product.name else ""
                    data['product_code'] = product.default_code or ""
                    
                    for supplier in product.seller_ids:
                        data['supplier'] = supplier.name.name or ""
                        data['supplier_name'] = translate(supplier.product_name) if supplier.product_name else "" #translate(supplier.product_name)
                        data['supplier_code'] = supplier.product_code or ""
                        data['delay'] = supplier.delay or ""
                        data['min_qty'] = supplier.min_qty or 1.0
                                    
                        for pricelist in supplier.pricelist_ids:
                            if pricelist.is_active:                            
                                data['price'] = pricelist.price or 0.0
                                data['min_quantity'] = pricelist.min_quantity or 1.0
                                data['quotation_date'] = "%s/%s/%s" % (
                                    pricelist.date_quotation[8:10],
                                    pricelist.date_quotation[5:7],
                                    pricelist.date_quotation[:4]) if pricelist.date_quotation else ""
                                write_line(file_csv, data)                

                        if not supplier.pricelist_ids:
                            write_line(file_csv, data)                

                    #if not product.seller_ids: # per ora stampo solo quelli che hanno il fornitore
                    #    write_line(file_csv, data)                
                except:
                    print "Error exporting: ", product.name, sys.exc_info()
            file_csv.close()
            
            return True
        except:
            return False
    
    def _create_report(self, cr, uid, report_name=False, file_name=False):
        #res_ids, 
        import netsvc
        if not report_name: #or not res_ids:
            return (False, Exception('Report name and Resources ids are required !!!'))
            
        try:
            ret_file_name = '/tmp/'+file_name+'.pdf'
            service = netsvc.LocalService("report." + report_name);
            (result, format) = service.create(cr, uid, [1], {}, {}) # res_id
            fp = open(ret_file_name, 'wb+');
            fp.write(result);
            fp.close();

        except Exception,e:
            print 'Exception in create report:',e
            return (False, str(e))
        return (True, ret_file_name)

    def create_report_and_save(self, cr, uid):
        import pdb; pdb.set_trace()
        self._create_report(cr, uid, "store_auto_report", "report_gpb")
        return True
        
    """def _function_get_partner_id(self, cr, uid, ids, args, field_list, context=None):
        ''' Search in default supplier code and return supplier ID
        '''
        res=dict.fromkeys(ids, 0)

        supplier_code=dict((item.name, item.id) for item in self.browse(cr, uid, ids))
        cr.execute("SELECT mexal_s, id from res_partner WHERE mexal_s in (" + ",".join(["%s",]*len(supplier_code)) + ")", supplier_code.keys())
        
        risultato=dict(cr.fetchall())
        lista=[(supplier_code[k], risultato[k]) for k in risultato.keys()]
        res.update(dict(lista))
        return res"""

        
    
    _columns = {
        'name':fields.char('Code', size=10, required=True, readonly=False),
        'suspended':fields.boolean('Suspended', required=False),        
        #'partner_id': fields.function(_function_get_partner_id, method=True, type='many2one', relation="res.partner", string='Partner', store=False),
    }
    
auto_stock_supplier()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
