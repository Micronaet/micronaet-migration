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


class dashboard_import_log(osv.osv):
    _name = 'dashboard.import.log'
    _description = 'Import log'
    
    _columns = {
               # General information:
               'name': fields.char('Event', size=64, required=False, readonly=False, help = 'Importation event name'),
               'start': fields.datetime('Date start'),
               'end': fields.datetime('Date stop'),
               'note': fields.text('Note', help="Info about event type"),
               'visible': fields.boolean('Visible', required=False),
               'days_error': fields.integer('Days error', help = 'Number of days before today that mark the event as error if not updated'),
               
               # Text for log importation:
               'ok': fields.text('Note', help="Info note"),
               'warning': fields.text('Note', help="Info note"),
               'error': fields.text('Note', help="Info note"),
               
               # Status:
               'status':fields.selection([
                   ('ok','OK'),
                   ('warning','Warning'),
                   ('error','Error'),                   
               ],'Status', select=True, readonly=False),
               }
    _defaults = {
        'visible': lambda *x: True,
        'status': lambda *x: 'ok',        
        'days_error': lambda *x: 1,        
        }           
dashboard_import_log()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
