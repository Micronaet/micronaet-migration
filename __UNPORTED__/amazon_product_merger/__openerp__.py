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
    'name' : 'Aamazon product merger',
    'version' : '0.0.1',
    'category' : 'Costomization/Migration',
    'description' : """ 
                    Module created for migrate DB product on another DB that
                    effectively connect with Amazon
                    (case study: 2 different Company/Ddatabase, A and B than 
                    migrate product in another Company/Database, this 3rd Company 
                    publish on Amazon an manages orders)
                    Usually A create product with default_code, B can integrate
                    his product or, using sku field migrate on exist default_code
                    product
                    """,
    'author' : 'Micronaet s.r.l.',
    'website' : 'http://www.micronaet.it',
    'depends' : [
                 'base',
                 'sale',
                 'log_and_mail',
                ],
    'init_xml' : [], 
    'update_xml' : [
                    'security/ir.model.access.csv',
                    'merger_views.xml',
                    'scheduler.xml',
                    'wizard/category_wizard.xml',
                   ],
    'demo_xml' : [],
    'active' : False, 
    'installable' : True, 
}
