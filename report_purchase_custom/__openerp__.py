###############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################################################
# Modified template model from:
#
# Micronaet s.r.l. - Nicola Riolini
# Using the same term of use
###############################################################################

{
	"name": "Aeroo Reports - Purchase",
	"version": "1.0",
	"description": "Report purchase order based on report_aeroo module",
	"author": "Nicola Riolini - Micronaet",
    'website': 'http://www.micronaet.it',
	"depends": [
	    "base", 
        "base_fiam", 
        "report_aeroo", 
        "report_aeroo_ooo",
        "purchase",
        "purchase_extra_field",
        ],
	"category": "Generic Modules/Aeroo Reporting",
	"init_xml": [],
	"demo_xml": [],
	"update_xml": [
        "purchase_view.xml",
        "report/report_order.xml",
        ],
	"installable": True
}

