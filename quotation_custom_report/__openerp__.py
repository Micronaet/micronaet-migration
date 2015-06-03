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
	"name": "Aeroo Reports - Quotation custom",
	"version": "1.0",
	"author": "Nicola Riolini - Micronaet",
    'website': "http://www.micronaet.it",
	"depends": [
	    "base",
        #"account", # TODO needed?
        "product",
        "sale",
        "report_aeroo",
        #"report_aeroo_ooo",
        #"sale_layout",
        "quotation_photo",
        ],
	"category": "Generic Modules/Aeroo Reporting",
	"init_xml": [],
	"demo_xml": [],
	"data": [
	    "order_line.xml",
	    "report/report_order.xml",
	    ],
	"installable": True
    }

