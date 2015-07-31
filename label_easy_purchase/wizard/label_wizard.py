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
        
        # -----------------
        # Start setup file:
        # -----------------
        root_path = os.path.dirname(openerp.addons.__file__) # addons path
        cmd_file = root_path + "/label_easy/wizard/csv/purchase.cmd" # Label
        bat_file = root_path + "/label_easy/wizard/csv/purchase.bat" # Command
        label_file = open(cmd_file, "w")

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
        for item in po_proxy.order_line: # loop on all lines:
            if not item.product_id:
                continue # jump line witout product            
            parameters['code'] = item.product_id.default_code
            # TODO need other params?

            # Windows path:
            path_label = "%s\\%s\\%s" % (
                wiz_proxy.label_id.path_id,
                wiz_proxy.label_id.folder,
                wiz_proxy.label_id.label_name[:-4],
                )
            bat_file.write(
                "formatname=\"%s\"\r\n" % (
                    path_label.replace("\\\\", "\\")))

            # TODO check the total of label to print
            bat_file.write("formatcount=%s\r\n" % item.product_qty)

            if i == 1:
               bat_file.write("testprint=off\r\n") # only one time

            # -----------
            # Parameters:
            # -----------
            for param in item.label_id.parameter_ids:
                if param.mode == 'static': # currently not used but leaved!
                   bat_file.write("%s=\"%s\"\r\n" % (
                       param.name, param.value))
                else: # dynamic
                   if param.mode_type in parameters and parameters[
                           param.mode_type]: # test if there is parameter
                       bat_file.write("%s=\"%s\"\r\n" % (
                           param.name, parameters[param.mode_type]
                           ))
                   else: # error param. not present!! erase not waste label
                      error.append(
                          "Parameter not found: %s" % param.mode_type)
                      # TODO raise one time or collect 

            # Be carefull: works with printer_id, write printer.number
            bat_file.write(
                "useprinter=%d\r\n" % wiz_proxy.printer_id.number)

            bat_file.write("jobdescription=\"%d) %s\"\r\n" % (
                   po_proxy.name, item.product_id.default_code))
                   
            if i == 1:
               bat_file.write("singlejob=on\r\n") # only one time
            bat_file.write(";\r\n") # end of record label
            i += 1
        bat_file.close()
        
        # ----------------------------
        # Create batch file to launch:
        # ----------------------------
        
        bat_file = open(FileOutputBat, 'w')
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
        bat_file.write(
            "@echo off\r\n" \
            "@net use o: %s /persistent:yes\r\n" % param_proxy[
                0].oerp_command + \
            "@copy o:\purchase.cmd \"%s\"\r\n" % (param_proxy[
                0].path, ) + \
            "@cd \"%s\"\r\n" %(param_proxy[
                0].path, ) + \
            "@cls\r\n" + \
            _("@echo Start printing... %s\r\n") % print_comment + \
            _("@echo Print note: %s\r\n") % wiz_proxy.note or _('No note!') + \
            "@pause\r\n" + \
            "@\"%s\\%s\" openerp\r\n" % (
                param_proxy[0].path,
                param_proxy[0].command,
                ))
        bat_file.close()
        return True
        
    _columns = {
        'note': fields.text('Note', help='Note for label employee'),
        'label_id': fields.many2one('easylabel.label', 'Label', required=True,
            domain=[('area', '=', 'purchase')]),
        'printer_id': fields.many2one('easylabel.printer', 'Printer', 
            required=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
