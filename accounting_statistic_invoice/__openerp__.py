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

{
    'name': 'Accounting statistic: invoice',
    'version': '0.1',
    'category': 'Statistic',
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'base_mssql_accounting', # for destination conversion
        'accounting_statistic_base',
        'production_family',
        'product_categorization',
        'sql_partner_agent', # for partner management
        'partner_tags',
        'base_location', # zip_id and other fields
        'purchase_extra_field', # first supplier filter
        ],
    'init_xml': [],
    'demo_xml': [],
    'data': [
        'security/ir.model.access.csv',        
        'invoice_view.xml',        
        'log_view.xml',
        'scheduler.xml',
        ],
    'active': False,
    'installable': True,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
