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
    'name': 'Syncro module for partner 5.0 > 8.0',
    'version': '0.0.1',
    'category': 'Syncro Migration',
    'description': """
        Procedure custom for migrate some objects
        """,
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        'base',
        'l10n_it_fiscalcode',
        'hr',
        'report_aeroo',
        'contacts',
        'calendar',
        'analytic',
        #'account_analytic_analysis',
        'hr_attendance',
        'hr_holidays',
        'hr_timesheet',
        #'hr_timesheet_invoice',
        #'hr_timesheet_sheet',
        'partner_addresses',
        #'analytic_contract_hr_expense',
        ],
    'init_xml': [], 
    'data': [
        'syncro_view.xml',
        'wizard/migrate_view.xml',
        ],
    'demo_xml': [],
    'active': False, 
    'installable': True, 
    }
