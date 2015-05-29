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

from osv import fields,osv

class search_database_wizard(osv.osv_memory):
    """ Search a string in database setting up un listed database and return
        result and the possibility to go in search in actual DB (res.partner)
    """
    _name = 'search.database.wizard'

    def return_view(self, cr, uid, name, res_id):
        '''General purpose function that return dict action for next step of
           the wizard
        '''
        return {
            'name': 'Searched partners',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': str([('id', 'in', res_id)]),
            }

    def search_text_in_other_database(self,cr, uid, ids, context=None):
        ''' Search button in wizard windows, search in other DB list and
            comunicate existence in other DB res.partner finded in list box
        '''
        import xmlrpclib

        # TODO parametrizzare:
        server='localhost'
        port='8069'
        user='admin'
        pwd='password'

        if context is None:
           context = {}

        # Read data in wizard form:
        wiz_proxy=self.browse(cr, uid, ids, context=context)
        search_string=wiz_proxy[0].name

        db_ids = self.pool.get('search.database').search(cr, uid, [
            ('search','=', True)], context=context)
        finded_result=""
        if db_ids: # if there is some DB in list:
           for db in self.pool.get('search.database').browse(
                   cr, uid, db_ids, context=context):
               dbname = db.name
               sock = xmlrpclib.ServerProxy(
                   'http://' + server + ':' + port + '/xmlrpc/common',
                   allow_none=True)
               uid_extra = sock.login(dbname ,user ,pwd)
               sock = xmlrpclib.ServerProxy(
                   'http://' + server + ':' + port + '/xmlrpc/object',
                   allow_none=True)

               partner_ids = sock.execute(
                   dbname, uid_extra, pwd, 'res.partner', 'search', [
                       ('name', 'ilike', search_string), ])
               if partner_ids:
                  partner_read = sock.execute(
                      dbname, uid_extra, pwd, 'res.partner', 'read',
                      partner_ids)
                  for partner in partner_read:
                      finded_result += "[%s] %s - (%s - %s) %s - %s\n" % (
                          dbname, partner['name'], partner['city'] or "",
                          partner['country'] and partner['country'][1],
                          partner['phone'] or "", partner['email'] or "")

        partner_current_ids = len(self.pool.get('res.partner').search(
            cr, uid, [('name', 'ilike', search_string)], context=context))
        # Change fields (status) of the wizard:
        wiz_result=self.write(cr, uid, ids, {
            'state': 'find',
            'find': finded_result,
            'current': partner_current_ids,
            })
        return True

    def search_text_in_database(self, cr, uid, ids, context=None):
        ''' Search button in wizard windows, search in current DB and
            comunicate existence in other DB res.partner finded
        '''

        if context is None:
           context = {}

        # Read data in wizard form:
        wiz_proxy = self.browse(cr, uid, ids, context=context)
        search_string = wiz_proxy[0].name

        # Cerco nell'attuale DB i partner che possono andare bene:
        partner_ids=self.pool.get('res.partner').search(
            cr, uid, [('name', 'ilike', search_string)], context=context)

        return self.return_view(cr, uid, '', partner_ids)

    _columns = {
                'name': fields.char('Text to search', size=60, required=True),
                'find': fields.text('Finded in other DB'),
                'current': fields.integer('Find current DB'),
                'state': fields.selection([
                    ('search','Search'),
                    ('find','Find in other DB'),
                ],'State', select=True, readonly=True),
               }

    _defaults = {
       'state': lambda *a: 'search',
       'current': lambda *a: 0,
                }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

