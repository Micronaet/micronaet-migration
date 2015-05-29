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
from datetime import datetime
import csv, pdb

class easylabel_batch_wizard(osv.osv_memory):
    '''Wizard for launch a procedure that import CSV file in 'csv' subfolder
       obviously this file will be previous copyed in this folder, in my 
       automation mechanism there is a macro that export the production sheet
       in yours, maybe, the file is generated from an account program directly
       Respect record trace of my file or create new modify import procedure.
       This is a nevralgical part of the program, start the input process that 
       generate the batch file for Easylabel command file...
    ''' 
    from datetime import datetime

    _name = 'easylabel.batch.wizard'

    def _printer_default_get(self, cr, uid, field, context = None):
        '''Get default printer according to field name (all 3 field for printers)'''
        printer_type=''  
        if field=='printer_art_id':
           printer_type='article'
        elif field=='printer_pac_id':
           printer_type='package'
        elif field=='printer_pal_id':
           printer_type='pallet'
        printer_ids=self.pool.get('easylabel.printer').search(cr, uid, [('type', '=', printer_type)], context=context)
        return printer_ids and printer_ids[0] or False # take the first

    def return_view(self, cr, uid, name, res_id):        
        '''Function that return dict action for next step of the wizard'''
        #view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name','=','view.name.p1')]) 
        return {
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'easylabel.batch', # object linked to the view
                #'views': [(view_id, 'form')],
                'view_id': False,
                'type': 'ir.actions.act_window',
                #'target': 'new',
                'res_id': res_id,  # ID selected
               }

    _columns = {
    'line': fields.char('Line of production', size=10, required=False, readonly=False),
    'week': fields.char('Actual week', size=10, required=False, readonly=False),     
    'note': fields.text('Note', help="Not mandatory, if present are append to new batch job imported!"),
    'printer_art_id':fields.many2one('easylabel.printer', 'Article Printer', required=False),
    'printer_pac_id':fields.many2one('easylabel.printer', 'Package Printer', required=False),
    'printer_pal_id':fields.many2one('easylabel.printer', 'Pallet Printer', required=False),
    'state':fields.selection([
        ('import','Import'),
        ('create','Create'),
        ('done', 'Done'),        
    ],'State', select=True, readonly=True),
    }

    _defaults={
              'state': lambda *a: 'import', 
              'week': lambda *a: datetime.strftime(datetime.now(),"%y%W"), # format: YYWW
              'printer_art_id': lambda self, cr, uid, c: self._printer_default_get(cr, uid, 'printer_art_id', context=c),
              'printer_pac_id': lambda self, cr, uid, c: self._printer_default_get(cr, uid, 'printer_pac_id', context=c),
              'printer_pal_id': lambda self, cr, uid, c: self._printer_default_get(cr, uid, 'printer_pal_id', context=c),
              }

    def import_csv(self,cr, uid, ids, context=None):
        '''Import function launched by the wizard'''

        if context is None:
           context={}

        def data_convert(valore):  
            # File come from Win P so in cp1252 format, not UTF-8, so convert!
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip() # returned without extra spaces

        def parse_order(value):
            '''Get header description and extract order number'''
            l=value.split("_")            
            return l[-2]

        def prepare_col_list(self, cr, uid, ids, col_list, line, header_line, note_line, date_line, cust_order_line, error, context=None):
            ''' Prepare col customer data in col_list format
                es. [(1, cod_cli, id, false (not present), et1, et2, et3, [p1, p2, p3, p4]), (2,cod_cli, true (present),et1, et2, et3, [p1, p2, p3, p4]),]
                Search label col parameter in other line:
                Parameter: p1='shipment' Delivery
                           p2='order'    Order number
                           p3='order_c'  Customer order    
                           p4='shipment_date' Delivery date  
                           # TODO DESTINATION!!!
                           #p4='customer' Customer     # yet present in line
                           #p5 'color'   Product color # in easylabel DB for now!
                           #p6 'size'    Product size  # in easylabel DB for now!'''
            for i in range(2, len(line)):
                cust_code = data_convert(line[i]) # code is: 06.12345
                cr.execute("""SELECT id, article_label_id, pack_label_id, pallet_label_id
                              FROM res_partner
                              WHERE mexal_c = %s""", (cust_code,))
                finded=False
                for item in cr.fetchall():
                    partner_id=item[0]
                    lab1 = item[1]
                    lab2 = item[2]
                    lab3 = item[3]
                    finded=True
                p1 = note_line[i]  # TODOnote is also DESTINATION
                p2 = parse_order(header_line[i]) # company order number
                p3 = cust_order_line[i] # customer order number
                p4 = date_line[i].replace(r"_",r"/") # order date (dead line)
                col_list.append((i-1, cust_code, partner_id, finded, lab1, lab2, lab3,[p1,p2,p3,p4])) 
                if finded==False:
                   error.append("Customer not found: %s" %(cust_code))   
            return

        def prepare_row_list(self, cr, uid, ids, row_list, line, error, context=None):
            ''' Prepare row data in row_list format
                es. [('cod art1', 'id', 'q_x_pack1', True (present), [va1, va2, va3, va4]), ('cod art2', 'q_x_pack2', False (not present), [vb1, vb2, vb3, vb4]),] '''
            value_list=['0' + x for x in line[2:]]  # add 0 on left
            value_list=[int(x) for x in value_list]     # so no error on convert in int (problem with '')
            art_code=data_convert(line[0])
            cr.execute("""SELECT id, q_x_pack
                          FROM product_product
                          WHERE mexal_id = %s """, (art_code,))
            finded=False
            label_id=0
            for item in cr.fetchall():
                q_x_pack = item[1]
                label_id= item[0]
                finded=True
                # TODO test if there is one!
            # TODO test for no items!!
            if label_id:
               row_list.append((art_code, label_id, q_x_pack, finded, value_list)) # TODO replace 0 with p x pack (no decode for numbers)
            else: 
               error.append("Label ID not found for %s" %(art_code,))
            return 

        def get_default_printer(self, cr, uid, ids, printer_list, error, context=None):
            '''Get a dictionary value for all type of label
               read printers property and get all default values
               after update the dictionary
            '''
            for k in printer_list.keys():
               cr.execute('''SELECT id, type 
                             FROM easylabel_printer 
                             WHERE type = %s ''', (k,))
               for item in cr.fetchall():
                   printer_list[k] = item[0]
            return 


        def create_label_list(self, cr, uid, ids, row_list, col_list, error, context=None):
            '''Function that prepare export grid for generate batch obect and total labels
            '''
            import operator # for mod operation

            def particularity_col_list(self, cr, uid, ids, col_list, row, context=context):
                '''Transform col list reading for each customer if there is 
                   some article particularity that need to replace label(_id) 
                   in printing
                ''' 
                import string
                col_list_clone=[] 
                for col in col_list:
                    label_ids=list(col[4:7]) # default are actual label_id
                    cr.execute('''SELECT id, parent_name, article_label_id, pack_label_id, pallet_label_id 
                                  FROM easylabel_particularity 
                                  WHERE partner_id = %s''', (col[2],))
                    for item in cr.fetchall(): # load all particularity and test match
                        #import pdb; pdb.set_trace()     
                        if string.find(row[0],item[1])>=0: #exist a part of code in article
                           # Change if exist, else default are leaved
                           for i in range(0,3):
                               if item[i + 2]: # test all label_id
                                  label_ids[i]=item[i + 2]  # if exist change default value saved                     
                    col_list_clone.append((col[0],col[1],col[2],col[3],label_ids[0],label_ids[1],label_ids[2],col[7])) 
                return  col_list_clone

            if context is None:
               context={}
           
            # Check for some characteristics:
            if not all([x[3] for x in col_list]): #Verify that all customer exist
               error.append("Not all customers are finded!")
               return
            # Check product if exist
            if not all([x[3] for x in row_list]): #Verify that all product
               error.append("Not all product are finded!")
               return
            # Check product if all lot quantity exist (>=1)
            if not all([x[2]>=1 for x in row_list]): #Verify that all product
               error.append("Not all product have lot quantity >=1")
               return
            # Create easylabel.batch
            wiz_proxy=self.browse(cr, uid, ids, context=context)
            batch_data={'name': datetime.strftime(datetime.now(),"Batch Work: %Y/%m/%d (%H:%M)"),}
            if len(wiz_proxy): # ==1
               batch_data['line']=wiz_proxy[0].line
               batch_data['week']=wiz_proxy[0].week
               batch_data['note']=wiz_proxy[0].note
            batch_id=self.pool.get('easylabel.batch').create(cr, uid, batch_data, context=context)
            context.update({'batch_id': batch_id,})
            
            # Create easylabel.batch.line for article, package, pallet
            sequence = 0
            label_type = ('article', 'package', 'pallet',)      
            printer_list = {'article':0, 'package':0, 'pallet':0,}  # default printer to use
            get_default_printer(self, cr, uid, ids, printer_list, error, context=context)      
            for row in row_list: # loop for row
                sequence += 1 # list counter 
                for gap_type in range(0,3): # step 3 label type
                    col_list_clone=particularity_col_list(self, cr, uid, ids, col_list, row, context=context) # error, 

                    for col in sorted(col_list_clone, key=lambda col_list_clone: col_list_clone[4 + gap_type]): # Sorted per label_id (article next lot net pallet)
                        total=row[4][col[0] - 1]
                        if total:
                            batch_line={'sequence': sequence,
                                        'position': "R%d-C%d" %(sequence, col[0]), # 
                                        'batch_id': batch_id,
                                        'printer_id': printer_list[label_type[gap_type]], # TODO rules
                                        'partner_id': col[2],
                                        'product_id': row[1],
                                        'type': label_type[gap_type],
                                        'label_id': col[4 + gap_type],
                                        'name': "%s" %(row[0],), # Trunkated if long!
                                        # Parameters:
                                        'shipment': col[7][0], # note field=shipment place!
                                        'order': col[7][1],
                                        'order_c': col[7][2],
                                        'shipment_date': col[7][3], # delivery date
                                       }
                            if label_type[gap_type]=='article':
                               batch_line['total']= total 
                               if row[2]>1: # pz x pack: not print article label if pz x pack=1 (only package)
                                  batch_line_id=self.pool.get('easylabel.batch.line').create(cr, uid, batch_line, context=context)
                            elif label_type[gap_type]=='package':
                               if operator.mod(total, row[2]): # approx over if there's a rest!
                                  rest=1
                               else:
                                  rest=0
                               batch_line['total']= (total / row[2]) + rest    
                               batch_line_id=self.pool.get('easylabel.batch.line').create(cr, uid, batch_line, context=context)
                            elif label_type[gap_type]=='pallet': # TODO (nothing for now!)
                               batch_line['total']= 0                   
                               #batch_line_id=self.pool.get('easylabel.batch.line').create(cr, uid, batch_line, context=context)
                            else:  # NOT EXIST!!
                               error.append("Type of label not found:")
            return

        def get_addons_path():
            '''Import addons module, read the path!'''
            import addons, os
            return os.path.dirname(addons.__file__) 

        FileInput = get_addons_path() + "/label_easy/wizard/csv/openerp.csv" 
        FileCSV=open(FileInput,'rb')
        lines = csv.reader(FileCSV, delimiter=';')   # Excel export with comma!     
        counter=0
        error=[] # String that collect list of import error
        tot_col=0
        col_list=[]  # es. [(1, cod_cli, et1, et2, et3), (2,cod_cli, et1, et2, et3),]
        row_list=[]  # es. [('cod art1', 'q_x_pack1', [va1, va2, va3, va4]), ('cod art2', 'q_x_pack2', [vb1, vb2, vb3, vb4]),] 
        tot_list=[]  # grid for all export data
        for line in lines:
            counter+=1
            if counter==1:  # get header line
               tot_col=len(line)
               header_line=line
            elif counter==2:
               note_line=line
            elif counter==3:
               date_line=line
            elif counter==4: # TODO convert to col_list
               customer_line=line
            elif counter==5:
               cust_order_line=line
               prepare_col_list(self, cr, uid, ids, col_list, customer_line, header_line, note_line, date_line, cust_order_line, error, context=context)
            else: # data lines:
               if len(line) != tot_col: # data col not equal to header col
                  error.append("%s Wrong column number %d instead %d in line %d" % (error, len(line), tot_col, counter)) # raise error?
               else: # right behaviour
                  prepare_row_list(self, cr, uid, ids, row_list, line, error, context=context)
        create_label_list(self, cr, uid, ids, row_list, col_list, error, context=context)                 
        # export_command_file(self, cr, uid, ids, error, context=context) # moved as a button in batch form
        FileCSV.close()
        if error: # TODO verify len or write in the form
           raise osv.except_osv("Error", error)
        #return {'type': 'ir.actions.act_window_close'} # Close the window  
        return self.return_view(cr, uid, 'easylabel_batch_form', context.get('batch_id', 0)) 

easylabel_batch_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

