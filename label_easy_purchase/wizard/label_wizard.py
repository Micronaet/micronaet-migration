# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import dbf
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class EasyLabelPurchaseWizard(orm.TransientModel):
    '''Wizard for export the list of label to be lauched on Easy Label PC
    '''
    _name = 'easylabel.purchase.wizard'

    # -------------
    # Event button:
    # -------------
    
    def export_label(self, cr, uid, ids, context=None):
        ''' This event generate the batch command to be launched from Easy
            label PC, after generate the command to print all the label in 
            correct order.
            After this the label employee have to launch the link on his 
            desktop PC 
        '''
        
        # ---------------------------------------------------------------------
        #                           Start setup file
        # ---------------------------------------------------------------------
        root_path = os.path.dirname(openerp.addons.__file__) # addons path
        
        # file name:
        cmd_file = root_path + "/label_easy/wizard/csv/purchase.cmd" # Label
        bat_file = root_path + "/label_easy/wizard/csv/purchase.bat" # Command
        dbf_file = root_path + "/label_easy/wizard/csv/purchase.dbf" # Database
        
        # file handle:
        label_file = open(cmd_file, "w")
        batch_file = open(bat_file, 'w')
        # TODO choose correct field:
        table = dbf.Table(dbf_file, # TODO correct? 
           'code C(18); desc C(80); colour C(40); ean C(12); imagine C(100); '
           'pack C(10); piece C(10); order C(30)')
        table.open()
        
        # ---------------------
        # Populate with labels:
        # ---------------------
        # Pool used:
        easylabel_pool = self.pool.get('easylabel.easylabel')
        po_pool = self.pool.get('purchase.order')
        
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        po_id = context.get('active_id', False) # TODO check!
        po_proxy = po_pool.browse(cr, uid, po_id, context=context)
        parameters = {} # used for merge in the label (postprocessor)
        i = 1
        label_to_print = '' # TODO for comunicate in batch
        for item in po_proxy.order_line: # loop on all lines:

            if not item.product_id:
                continue # jump line witout product            

            # Add record in database:
            default_code = item.product_id.default_code
            # TODO chose correct field:
            ean = item.product_id.ean13[:12] if item.product_id.ean13 else ''
            name = item.product_id.name.split("] ")[-1]
            try:
                colls = int(element.product_id.colls) or 1
            except:
                colls = 1
            try:
                q_x_pack = int(element.product_id.q_x_pack) or '/'
            except:
                q_x_pack = '/'

            # Write record in database:
            table.append((
                default_code, 
                name, 
                item.product_id.colour, 
                ean,
                'C:\Immagini\%s.jpg' % default_code, 
                '0', # Pack TODO not used, remove!!! (also in label)
                q_x_pack, # Pieces
                item.order_id.name,
                ))

            # Windows path:
            path_label = "%s\\%s\\%s" % (
                wiz_proxy.label_id.path_id,
                wiz_proxy.label_id.folder,
                wiz_proxy.label_id.label_name[:-4],
                )

            # Loop on label for colls:
            for part in range(1, colls + 1): 
                # Parameter to pass during print (cmd file):
                partno = "%s/%s" % (part, colls)
                parameters['code'] = default_code
                parameters['partno'] = partno
                # TODO need other params?

                label_file.write(
                    "formatname=\"%s\"\r\n" % (
                        path_label.replace("\\\\", "\\")))

                # TODO check the total of label to print
                tot_label = 1 if wiz_proxy.test else int(item.product_qty) 
                label_file.write("formatcount=%s\r\n" % tot_label)

                if i == 1 and part == 1: # first loop first part number
                   label_file.write("testprint=off\r\n") # only one time

                # -----------
                # Parameters:
                # -----------
                for param in wiz_proxy.label_id.parameter_ids:
                    if param.mode == 'static': # currently not used but leaved!
                       label_file.write("%s=\"%s\"\r\n" % (
                           param.name, param.value))
                    else: # dynamic
                       if param.mode_type in parameters and parameters[
                               param.mode_type]: # test if there is parameter
                           label_file.write("%s=\"%s\"\r\n" % (
                               param.name, parameters[param.mode_type]
                               ))
                       else: # error param. not present!! erase not waste label
                          error.append( # TODO raise one time or collect
                              "Parameter not found: %s" % param.mode_type)

                # Be carefull: works with printer_id, write printer.number
                label_file.write(
                    "useprinter=%d\r\n" % wiz_proxy.printer_id.number)

                label_file.write(
                    _("jobdescription=\"Order: %s (%s Part: %s)\"\r\n") % (
                        po_proxy.name, default_code, partno))

                if i == 1 and part == 1:
                    label_file.write("singlejob=on\r\n") # only one time
                    
                label_file.write(";\r\n") # end of record label
                label_to_print += "@echo Code %s  -  Tot. %s (%s) %s\r\n" % (
                    default_code, 
                    tot_label, 
                    partno,
                    '*test' if wiz_proxy.test else '',
                    )
                i += 1
        label_file.close()
        table.close()
        
        # ----------------------------
        # Create batch file to launch:
        # ----------------------------        
        param_ids = easylabel_pool.search(
            cr, uid, [], context=context)
        if not param_ids:
           error.append('Error, Some parameter not found!')
           raise osv.except_osv("Error", error)
           return False

        param_proxy = easylabel_pool.browse(
            cr, uid, param_ids, context=context)
        print_comment = ("%s [%s]" % (
            po_proxy.name, po_proxy.partner_id.name)
            ).replace('\'', '').replace('"', '')
        
        # TODO parametrize mapped drive and print message
        batch_file.write(
            "@echo off\r\n" \
            "@net use o: %s /persistent:yes\r\n" % param_proxy[
                0].oerp_command + \
            "@copy o:\purchase.cmd \"%s\"\r\n" % (param_proxy[
                0].path, ) + \
            "@copy o:\purchase.dbf \"%s\"\r\n" % (param_proxy[
                0].path, ) + \
            "@cd \"%s\"\r\n" %(param_proxy[
                0].path, ) + \
            "@cls\r\n" + \
            _("@echo Start printing... %s\r\n") % print_comment + \
            _("@echo Print note: %s\r\n") % (
                wiz_proxy.note or _('No note!'), ) + \
            _("@echo Job detail:\r\n%s\r\n") % label_to_print + \
            "@pause\r\n" + \
            "@\"%s\\%s\" purchase\r\n" % (
                param_proxy[0].path,
                param_proxy[0].command,
                ))
        batch_file.close()
        return True
        
    _columns = {
        'label_id': fields.many2one('easylabel.label', 'Label', required=True,
            domain=[('area', '=', 'purchase')]),
        'printer_id': fields.many2one('easylabel.printer', 'Printer', 
            required=True),
        'test': fields.boolean('Print test', 
            help='The print test launch a batch job with 1 label for all'),
        'note': fields.text('Note', help='Note for label employee'),
        'run_note': fields.text('Procedure', readonly=True,
            help='Help user with the procedure'),
        }
    _defaults = {
        'test': lambda *x: False,
        'run_note': lambda *x: '''
            <p><h1>Export label procedure:</h1>
               Choose the purchase label for print this order and the default
               printer to use, after export all the command file with the
               button. <br/>
               To print the label run the batch on print workstation (destkop)
               link, ensure that the printer correct is open and with the right
               labels.
            </p>
            ''',
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
