##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
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
##############################################################################

from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.counters = {}
        self.localcontext.update({
            'clean_description': self.clean_description,
            'get_telaio': self.get_telaio,
            'get_fabric': self.get_fabric,
            'set_counter': self.set_counter,
            'get_counter': self.get_counter,
            
            # TODO remove
            'temp_get_order': self.temp_get_order,
        })

    def temp_get_order(self):
        pool = self.pool.get('product.product')
        item_ids = pool.search(self.cr, self.uid, [])
        return pool.browse(self.cr, self.uid, item_ids)
        
    def set_counter(self, name, value = 0.0):
        ''' Create or set a counter in the counter list of the class
            If value is not setted counter is reset
        '''
        self.counters[name] = value
        return

    def get_counter(self, name):
        ''' Return counter value, if present, else 0.0
        '''
        return self.counters.get(name, 0.0)

    def clean_description(self, name):
        return name.split("]")[-1:]

    def get_fabric(self, code, language):
        ''' Return type of fabric depend on start code
        '''
        code = code.upper()
        if code[3:6] == "TXI":
            if language == 'it_IT':
                return "Texfil ignifugo"
            else:    
                return "Texfil fire retardant"
                
        elif code[3:6] == "TXR" or code[3:5] == "TX":
            if language == 'it_IT':
                return "Texfil"
            else:    
                return "Texfil"

        elif code[3:5] == "PE":
            if language == 'it_IT':
                return "Poliestere"
            else:    
                return "Polyester"

        elif code[3:5] == "S3":
            if language == 'it_IT':
                return "Triplex"
            else:    
                return "Triplex"
    
        elif code[3:5] == "SB" or code[3:4] == "S":
            if language == 'it_IT':
                return "Olefine"
            else:    
                return "Olefine"

        elif code[3:4] == "L" or code[3:5] == "IL":
            if language == 'it_IT':
                return "Acrypol"
            else:    
                return "Acrypol"

        else:        
            return "/"        

    def get_telaio(self, name, lingua):
        if name:
            name=name.strip()
            if name == "STEEL":
               name = "ACCIAIO"
            ita2eng = {
               "ALLUMINIO": "ALUMINIUM", 
               "LEGNO": "WOOD", 
               "ACCIAIO": "STEEL"}
            if lingua != 'it_IT':
               return ita2eng[name] if name in ita2eng else "?"
            else:
               return name
        else:       
            return ""
