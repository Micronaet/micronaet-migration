# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://axelor.com) All Rights Reserved.
# Copyright (c) 2010-2011 Micronaet  SRL. (http://www.micronaet.it) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
import datetime

class easylabel_easylabel(osv.osv):
    '''Parameter of PC that have easylabel installed
    '''
    _name = 'easylabel.easylabel'
    _description = "Easylabel"

    _columns = {
               'name': fields.char('PC Name', size=32, required=False, readonly=False, help="Name of the PC that have installed Easylabel"), # TODO multiple PC
               'path': fields.char('Easylabel Path', size=256, required=False, readonly=False, help=r"Complete path of the root folder, ex.: c:\programmi\tharo\easylabel"),
               'command': fields.char('EXE Command', size=32, required=False, readonly=False, help=r"File that launch the batch command, ex.: easy.exe"),
               'oerp_command': fields.char('Openerp network path', size=256, required=False, readonly=False, help=r"\\192.168.100.181\easylabel"),
               }
easylabel_easylabel()

class easylabel_path(osv.osv):
    '''List of possible path, used to not repeat, with error risk
       in the name of the label, so there is this list for various
       path with the possibility do add in label a sub folder block 
       ending with tha name of the label
       So the label path is:
       (this root path) + (label subfolders) + (name of the label)
    '''
    _name = 'easylabel.path'
    _description = "Root path of label's folder"

    _columns = {
               'name':fields.char('Name', size=32, required=False, readonly=False, help="Short name to identify the folder"),
               'path': fields.char('Path', size=128, required=False, readonly=False, help=r"Complete path of the root folder, ex.: c:\easylabel\label\year2011"),
               'note': fields.text('Note', help="A little explaination of what folder contains"),
               }
    _order = "name"
easylabel_path()

class easylabel_label(osv.osv):
    '''Label Object to list all Easylabel FMT label created.
       When a new label is created on Easylabel, is mandatory 
       an integration in this object. Also for the parameter of
       command file, so when new column is added must added also here.
    ''' 
    _name = 'easylabel.label'
    _description = 'List of label in Easylabel'

    _columns = {
        'name': fields.char('Name', size=64, required=False, readonly=False, help="Friendly name of the label"),
        'label_name': fields.char('Label Name', size=64, required=False, readonly=False, help="Name of the label in Easylabel program"),
        'height': fields.float('Height', help="Height of label in mm."), 
        'width': fields.float('Width', help="Width of label in mm."), 
        'lot': fields.integer('Lot'),
        'folder': fields.char('Extra folder', size=128, required=False, readonly=False, help="Extra folder to added to root one."),
        'root_id':fields.many2one('easylabel.path', 'Root folder', required=False, help="Root folder zone"),
        'path_id': fields.related('root_id','path', type='char', size=128, string='Root path folder'),        
        'type':fields.selection([
            ('article','Article'),
            ('package','Package'),            
            ('pallet','Pallet'), 
            ('placeholder', 'Placeholder'),           
        ],'Type of label', select=True, readonly=False),
        'counter':fields.boolean('Has counter', required=False, help='Has a parameter that write for each lot number / tot value'),        
        }

    _defaults = {
                'type': lambda * a: 'article',
                'lot': lambda *a: 1,
                'counter': lambda *a: False,
                }

easylabel_label()

class easylabel_parameter(osv.osv):
    '''List of parameter for command file for the label.
       The list of param must be in the same order of the 
       colums param in the label of Easylabel. Any variation
       in easylabel parameter must be update here.
    '''
    _name = 'easylabel.parameter'
    _description = 'Label command file parameter'

    _columns = {
        'name':fields.char('Parameter', size=32, required=False, readonly=False),
        'sequence': fields.integer('Sequence'),
        'label_id': fields.many2one('easylabel.label', 'Label', required=False),                 
        'mode': fields.selection([
            ('static','Static'),
            ('dynamic','Dynamic'),],
            string="Mode",
            help="Static if text is always the same, dynamic if use some automatism: need compilation of 'mode type'!"),  
        'mode_type':fields.selection([
            ('date','Today date'),
            ('week','Today week'),
            ('shipment','Place of shipment'), 
            ('shipment_date','Date of shipment'), 
            ('order','Order number'),
            ('order_c','Customer order number'),
            ('code','Product code'),
            ('product','Product description'),
            #('color','Product color'), # for now in easylabel DB
            #('size','Product size'),   # for now in easylabel DB
            ('line','Line of production'),
            ('counter','Counter'),           # Counter (create one label for all pack label)
            ('counter_tot','Counter total'), # Total number of lots
            ],
            string="Mode",
            help="If mode is Dynamic set up here the field automatic value"),  
        'value':fields.char('Value', size=32, required=False, readonly=False, help="Value for static text"),
        }
          
    _defaults = {
                'mode': lambda * a: 'dynamic',
                }

easylabel_parameter()

class easylabel_batch(osv.osv):
    '''Batch block that are to be manage as spool block to send
       via "command file" to the printer, so the entire block
       will be printed one time.
    '''

    _name = 'easylabel.batch'
    _description = 'Batch block of labels job'


    def export_command_file(self, cr, uid, ids, context=None):
        '''Export a command file for the list of label in easylabel.batch.line 
           elements
           Get path where to write from parameters
           Create batch file for launch the label from Easylabel  
           TODO: remove: context with batch_id
        '''
        from datetime import datetime

        if context is None:
           context={}
        error=[]
        # Functions:
        def get_addons_path():
            '''Import addons module, read the path!'''
            import addons, os
            return os.path.dirname(addons.__file__) 

        def create_ph_list(self, cr, uid, ph_ids, context=None):
            ''' Read all labels marked as placeholder and load the array:
                [(id_label, width, height),]'''
            cr.execute("""SELECT id, width, height
                          FROM easylabel_label
                          WHERE type='placeholder'""")
            for item in cr.fetchall():
                ph_ids.append(item)             
            return 

        def write_placeholder(self, cr, uid, old_value, ph_ids, printer_id, obj_file, context=None):
            '''Search a placeholder label for this witdh, value
               Get comment parameter to fill
               Prepare output text with old value printed
               Write label to file setting up right printer'''
            for ph in ph_ids: # search right placeholder according to measure
                if ph[1]==old_value[printer_id][2] and ph[2]==old_value[printer_id][3]: # test width and height
                   ph_id=ph[0] # save label_id
                   continue # exit for
            if not ph_id:
               # TODO raise error for no PH found with measure
               pass
            
            item=self.pool.get('easylabel.label').browse(cr, uid, ph_id, context=context) # Read the only item found!
            path_label = "%s\\%s\\%s" %(item.path_id, item.folder, item.label_name[:-4])
            obj_file.write("formatname=\"%s\"\r\n" %(path_label.replace("\\\\", "\\"),))
            obj_file.write("formatcount=1\r\n")
            obj_file.write("%s=\"Cod:%s,Etic:%s,Tot:%s\"\r\n" %(item.parameter_ids[0].name, #'COMMENTO'
                                                                         old_value[printer_id][0],
                                                                         old_value[printer_id][1],
                                                                         old_value[printer_id][4],)) # TODO label name!
            obj_file.write("useprinter=%d\r\n" %(printer_id,)) # TODO: set number not id!!
            obj_file.write("jobdescription=\"Fine blocco\"\r\n")
            obj_file.write(";\r\n") # end of record label
            return
    
        def create_old_value(self, cr, uid, old_value, context=None):
            '''Read printer list and generate the dictionary that is 
               necessary for test break code in label'''
            cr.execute("""SELECT id, number FROM easylabel_printer""")
            for item in cr.fetchall():
                old_value[item[1]]=['',0,0,0,0]  # printer: ['art code', label_id, width, height, # total]
            return

        addons_path = get_addons_path()           
        FileOutput = addons_path + "/label_easy/wizard/csv/openerp.cmd" 
        FileOutputBat = addons_path + "/label_easy/wizard/csv/openerp.bat" 
        
        # Read easylabel.batch parameters (header parameters)       
        if not ids: # test context read of batch ID
           error.append("Not found batch ID!")
           return

        batch_param_proxy= self.browse(cr, uid, ids[0]) # read batch header for param.
        parameters={ # list of parameters that are available on batch header o computed!
                    'date': datetime.now().strftime('%d-%m-%Y'), # Today date
                    'week': batch_param_proxy.week or datetime.strftime(datetime.now(),"%y%W"), # number of a week format: yyww
                    'line': batch_param_proxy.line or '', # Line of production
                    #'shipment': ,#Date of shipment
                    #'order': ,   #Order number
                    #'code': ,    #Product code
                    #'product': , #Product description
                    #'color':   , #Product color
                    #'size': ,    #Product size
                   }
        fileObj = open(FileOutput,"w") 
        i=1               
        ph_ids=[] # list of all placeholder, ([id, width, height),]
        create_ph_list(self, cr, uid, ph_ids, context=context)

        old_value= {}
        create_old_value(self, cr, uid, old_value, context=context) # List of last value for each printers: (art code, label_id, width, height)
        
        for item in batch_param_proxy.line_ids: # for each label in the list
            # Read easylabel.batch.line parameters (line parameters) (write off everytime)
            parameters['code'] = item.product_id and item.product_id.code or ''  # Product code
            parameters['product'] = item.product_id and item.product_id.description_sale or ''  # Product description
            parameters['shipment'] = item.shipment             # Place of shipment
            parameters['shipment_date'] = item.shipment_date   # Date of shipment
            parameters['order'] = item.order                   # Order number
            parameters['order_c'] = item.order_c               # Order number
            #parameters['color']= product_id and item.product_id.code or ''    # Product color
            #parameters['size']=                               # Product size
            #parameters['counter']="1"                         # Counter (create one label for all pack label) > moved in loop
            parameters['counter_tot']=item.total               # Total number of lots
        
            # Write a label object
            if not item.label_id.name: # test if there's a label
               error.append("Error, Code %s, Some label not found (check customer setup) !" %(item.product_id.code,))
               raise osv.except_osv("Error", error) # TODO: stop or warn only??
               return False
          
            if not old_value[item.printer_id.id][1]: # Test if label_id exist (if not is the first value!)
               old_value[item.printer_id.id]=[item.product_id.code, # set up old value the first time
                                              item.label_id.id,
                                              item.label_id.width,
                                              item.label_id.height,
                                              0,]

            # Testing break code in                article code          or                                      label_id:
            if (old_value[item.printer_id.id][0] != item.product_id.code) or (old_value[item.printer_id.id][1] != item.label_id.id):
               write_placeholder(self, cr, uid, old_value, ph_ids, item.printer_id.id, fileObj, context=context)
               old_value[item.printer_id.id]=[item.product_id.code, # update old value with actual
                                              item.label_id.id,
                                              item.label_id.width,
                                              item.label_id.height,
                                              0,] # total
            old_value[item.printer_id.id][4] += item.total # add total number of labels!
               
            if item.label_id.counter: # set up if there is a loop to do
               loop=item.total  # n times
            else:
               loop=1           # once
            
            for step in range(0,loop):
                parameters['counter']=step + 1          # Counter (create one label for all pack label)            
                path_label = "%s\\%s\\%s" %(item.label_id.path_id, item.label_id.folder, item.label_id.label_name[:-4])
                fileObj.write("formatname=\"%s\"\r\n" %(path_label.replace("\\\\", "\\"),))
                if loop > 1: # counter labels!
                   fileObj.write("formatcount=1\r\n") # write 1!
                else:  # test if there is lot number
                   if item.label_id.lot and item.label_id.lot>1:
                      fileObj.write("formatcount=%s,%d\r\n" %(item.total,item.label_id.lot))
                   else:
                      fileObj.write("formatcount=%s\r\n" %(item.total,))
                if i==1: 
                   print_comment=item.batch_id.name # only the first time (is equal!)
                   fileObj.write("testprint=off\r\n") # only one time
                # Parameters
                for param in item.label_id.parameter_ids:
                    if param.mode=='static':
                       fileObj.write("%s=\"%s\"\r\n" %(param.name, param.value,)) 
                    else: # dynamic
                       if param.mode_type in parameters and parameters[param.mode_type]: # test if there is parameter
                          fileObj.write("%s=\"%s\"\r\n" %(param.name, parameters[param.mode_type],)) 
                       else: # error parameter non present!! raise for not waste label!!!
                          error.append("Parameter not found: %s" %(param.mode_type,))
                          # TODO raise one time or collect and raise at the end? best second guess!

                fileObj.write("useprinter=%d\r\n" %(item.printer_id.number,)) # Be carefull: works with printer_id, write printer.number
                #fileObj.write("displaymsg=%s" %(item.label_id.total,)) 
                if loop > 1: # counter labels!
                   fileObj.write("jobdescription=\"%d) %s#%d\"\r\n" %(item.sequence, item.name,(step+1)))
                else:  
                   fileObj.write("jobdescription=\"%d) %s\"\r\n" %(item.sequence, item.name,))
                if i==1: 
                   fileObj.write("singlejob=on\r\n") # only one time
                fileObj.write(";\r\n") # end of record label
                i+=1

        fileObj.close()
        # Create batch file to launch
        fileObj = open(FileOutputBat,"w")                 
        param_ids_proxy= self.pool.get('easylabel.easylabel').search(cr, uid, [])
        if not param_ids_proxy:
           error.append("Error, Some parameter not found!")
           raise osv.except_osv("Error", error)
           return False

        param_proxy= self.pool.get('easylabel.easylabel').browse(cr, uid, param_ids_proxy)
        # TODO parametrize mapped drive and print message
        fileObj.write("@echo off\r\n" \
                      "@net use o: %s /persistent:yes\r\n" %(param_proxy[0].oerp_command,) + \
                      "@copy o:\openerp.cmd \"%s\"\r\n" %(param_proxy[0].path,) + \
                      "@cd \"%s\"\r\n" %(param_proxy[0].path,) + \
                      "@cls\r\n" + \
                      "@echo Inizio stampa %s\r\n" %(print_comment,) + \
                      "@pause\r\n" + \
                      "@\"%s\\%s\" openerp\r\n" %(param_proxy[0].path, param_proxy[0].command)) 
        fileObj.close()
        # TODO update as printed!
        
        return True

    _columns = {
        # Description fields:
        'name':fields.char('Name of print queue', size=32, required=False, readonly=False),
        'date': fields.date('Load date'),
        'state':fields.selection([
            ('unprinted','To be printed'),
            ('printed','Printed'),
            ('cancel','Cancelled'),
        ],'State', select=True, readonly=True),
        # Batch parameters:
        'line': fields.char('Line of production', size=10, required=False, readonly=False),
        'week': fields.char('Actual week', size=10, required=False, readonly=False),     
        'note': fields.text('Note',),
        }
    _order="date"
    _defaults = {
                'date': lambda * a: datetime.datetime.now(),
                'state': lambda * a: 'unprinted',
                }

easylabel_batch()

class easylabel_label_inherit(osv.osv):
    '''Adding extra relation fields with tables
    '''
    _name = 'easylabel.label'
    _inherit = 'easylabel.label'  

    _columns = {
               'parameter_ids':fields.one2many('easylabel.parameter', 'label_id', 'Parameter', required=False),                   
               } 
easylabel_label_inherit()

class easylabel_particularity(osv.osv):
    '''List of particularity label, usually for every
       Partner there is 3 label, this list ovverride
       default choice with the 3 (2 or 1) choosen in this object
    '''
    _name = 'easylabel.particularity'
    _description = 'Particularity'

    _columns = {
              'name':fields.char('Description', size=64, required=False, readonly=False),              
              'partner_id': fields.many2one('res.partner', 'Partner', required=False),                 
              'article_label_id':fields.many2one('easylabel.label', 'Article Label', required=False),
              'pack_label_id':fields.many2one('easylabel.label', 'Package Label', required=False),
              'pallet_label_id':fields.many2one('easylabel.label', 'Pallet Label', required=False),
              'parent_name':fields.char('Parent code', size=18, required=False, readonly=False, help='Begin of code, ex.:127 or whole code:127TX  BX'),
              # product.product ?? 
              }
easylabel_particularity()

class res_partner_easylabel(osv.osv):
    '''Add extra fields to res.partner for manage
       label, each partner has 3 type of labels:
       Article, Package, Pallet
       The program will print the label article for all art request,
       number of label package, searching on product packaging (tot / num for pack) 
       TODO: rules for get number of pallet total label (maybe adding Tot art for pallet
       to add on product.product object)
    '''
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
               'article_label_id':fields.many2one('easylabel.label', 'Article Label', required=False),
               'pack_label_id':fields.many2one('easylabel.label', 'Package Label', required=False),
               'pallet_label_id':fields.many2one('easylabel.label', 'Pallet Label', required=False),  
               'particularity_ids':fields.one2many('easylabel.particularity', 'partner_id', 'Particularity', required=False),                            
               } 
res_partner_easylabel()

class easylabel_printer(osv.osv):
    '''List of printer installed on Easylabel.
    '''
    _name = 'easylabel.printer'
    _description = 'Printers'

    _columns = {
        'name':fields.char('Printer name', size=32, required=False, readonly=False, help="Better if is the same in Easylabel"),
        'number': fields.integer('Number', help="Number in easylabel printers list"),
        'sequence': fields.integer('Sequence', help="Sequence order of priority"),
        'note': fields.text('Note', help="Describe usual format loaded or the final use of the printer."),        
        'type':fields.selection([
            ('article','Article'),
            ('package','Package'),            
            ('pallet','Pallet'),],
            string="Default type",
            help="Choose the default type of label this printer is for"),  
        }
    _order="sequence"
easylabel_printer()

class easylabel_batch_line(osv.osv):
    '''Each line is linked to the bacth block, and represents
       a single job of label print, so a list of the same label
       for a particular customer, for a particular product
    '''

    _name = 'easylabel.batch.line'
    _description = 'Batch block lines of labels job'

    _columns = {
        'name': fields.char('Element', size=64, required=False, readonly=False),
        'sequence': fields.integer('Sequence'),
        'position': fields.char('Position', size=10, required=False, readonly=False, help='Position in excel file, es.: R1-C5'),
        'batch_id':fields.many2one('easylabel.batch', 'Batch block', required=False, ondelete='cascade'),
        'printer_id':fields.many2one('easylabel.printer', 'Printer', required=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'product_id':fields.many2one('product.product', 'Product', required=False),
        'package_id' : fields.related('product_id','q_x_pack', type='integer', string='Package'),
        'total': fields.integer('Total of labels', help="Total number of label to be printed for this element"),        
        'type':fields.selection([
            ('article','Article'),
            ('package','Package'),            
            ('pallet','Pallet'),],
            string="Type of label",
            help="Type of label to be printed for this element"),  
        # Labels:
        'label_id':fields.many2one('easylabel.label', 'Use label', help="If present this label is used instead of the default partner label", required=False),
        'article_label_id': fields.related('partner_id','article_label_id', type='many2one', relation='easylabel.label', string='Partner article label'),
        'pack_label_id': fields.related('partner_id','pack_label_id', type='many2one', relation='easylabel.label', string='Partner package label'),
        'pallet_label_id': fields.related('partner_id','pallet_label_id', type='many2one', relation='easylabel.label', string='Partner pallet label'),
        # Parameters:
        'shipment': fields.char('Shipment place', size=25, required=False, readonly=False),
        'shipment_date': fields.char('Shipment date', size=25, required=False, readonly=False),
        'order': fields.char('Order', size=15, required=False, readonly=False),
        'order_c': fields.char('Customer order', size=15, required=False, readonly=False),
        }
    _order="sequence"
easylabel_batch_line()

class easylabel_batch_inherit(osv.osv):
    '''Adding extra relation fields on batch element
    '''
    _name = 'easylabel.batch'
    _inherit = 'easylabel.batch'  

    _columns = {
               'line_ids':fields.one2many('easylabel.batch.line', 'batch_id', 'Elements', required=False),                   
               } 
easylabel_batch_inherit()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
