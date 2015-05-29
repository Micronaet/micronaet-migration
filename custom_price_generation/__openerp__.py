# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# Copyright (c) 2010-2011"Micronaet s.r.l.". (http://www.micronaet.it) 
#                    All Rights Reserved.
#                    General contacts <info@micronaet.it>
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
    'name': 'Custom price for manage pricelist generation',
    'version': '0.0.1',
    'category': 'Generic Modules/Customization',
    'author': 'Micronaet s.r.l.',
    'website': 'http://www.micronaet.it',
    'depends': [
        'base',
        #'product',
        #'base_fiam',
        'sale',
        #'report_aeroo',
        'custom_price_generation',
        ],
    'init_xml': [], 
    'update_xml': [
        'security/ir.model.access.csv',
        #'product_views.xml',
        #'report/pricelist.xml', 
        ],
    'demo_xml': [],
    'active': False, 
    'installable': True, 
    }
