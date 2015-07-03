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

{
    'name': 'Syncro module for partner 6.0 > 8.0',
    'version': '0.0.1',
    'category': 'Syncro Migration',
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        # All this module are necessary for basic installation of ODOO
        'base',
        'report_aeroo',
        'partner_addresses',
        'product',
        'sale',
        'crm',
        'report_auto_stock',
        #'auto_backup',
        'report_aeroo',
        ],
    'init_xml': [], 
    'data': [
        'security/ir.model.access.csv',
        'syncro_view.xml',
        'wizard/migrate_view.xml',
        ],
    'demo_xml': [],
    'active': False, 
    'installable': True, 
    }
