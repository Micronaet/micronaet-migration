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
import os
import sys
import logging
from openerp.osv import fields, osv, expression, orm

_logger = logging.getLogger(__name__)


class ProductProductStartHistory(orm.Model):
    """ Model name: ProductProductStartHistory
    """

    _name = 'product.product.start.history'
    _description = 'Start history'
    _rec_name = 'product_id'

    def history_start_elements(
            self, cr, uid, mx_start_date=False, context=None):
        """ Save current history
        """
        if not mx_start_date:
            _logger.error('Cannot history without start date!')
            return False

        # Remove previous history values:
        history_ids = self.search(cr, uid, [
            ('mx_start_date', '=', mx_start_date),
            ], context=context)
        _logger.warning(
            'Delete previous record (in history): %s' % len(history_ids))
        self.unlink(cr, uid, history_ids, context=context)

        # Update with current:
        product_pool = self.pool.get('product.product')
        product_ids = product_pool.search(cr, uid, [], context=context)
        total = len(product_ids)
        i = 0
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
            i += 1
            if i % 100 == 0:
                _logger.warning('Updated %s of %s' % (
                    i, total,
                    ))

            self.create(cr, uid, {
                'product_id': product.id,
                'mx_start_date': product.mx_start_date,
                'mx_start_qty': product.mx_start_qty,
                }, context=context)
        return True

    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product', required=True),

        'mx_start_date': fields.date('Start date'),
        'mx_start_qty': fields.float(
            'Inventory start qty',
            digits=(16, 2),  # TODO parametrize
            help='Inventory at 1/1 for current year'),
    }
