# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'BOM price report',
    'version': '0.0.1',
    'category': 'Generic Modules/Customization',
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        'base',
        'mrp',
        'bom_total_component', # for bom component
        'report_aeroo',
        ],
    'init_xml': [], 
    'data': [
        "security/bom_group.xml",
        "report/report_bom.xml", 
        "bom_view.xml",
        "wizard/duplicate_view.xml", 
        ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
    }
