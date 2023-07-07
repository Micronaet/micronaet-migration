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
import os
import pdb
import sys
import io
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
import base64
import urllib
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class SaleOrderQuotation(orm.Model):
    """ sale.order extra fields
    """
    _inherit = 'sale.order'

    def extract_quotation_excel(self, cr, uid, ids, context=None):
        """ Extract quotation
        """
        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def format_lang(value, lang):
            """ Format date in lang
            """
            if not value:
                return ''

            if lang == 'it_IT':
                return '%s/%s/%s' % (
                    o.date_order[8:10],
                    o.date_order[5:7],
                    o.date_order[2:4],
                    )
            else:
                return  '%s/%s/%s' % (
                    o.date_order[8:10],
                    o.date_order[5:7],
                    o.date_order[2:4],
                    )

        # ---------------------------------------------------------------------
        # XXX Function from parser:
        # ---------------------------------------------------------------------
        # COMPANY 2:
        """def get_partner_address(self, order):
            ''' Return format destination address or current address
            '''
            if order.destination_partner_id: # destination address
                partner = order.destination_partner_id
            else: # partner address
                partner = order.partner_id
            return '%s\n%s %s %s %s' % (
                partner.name, 
                partner.street or '',  
                partner.zip or '', 
                partner.city or '', 
                partner.country_id.name or '',
                )
                
        def get_partner_return_info(self, order):
            ''' Extra data for return goods
            '''
            if (order.partner_id.lang or 'en_US') == 'en_US':
                mask = 'Delivery terms: %s\nPayment terms: %s'        
            else:
                mask = 'Resa merce: %s\nPagamento: %s'
            return mask % (
                order.return_id.text or '',
                order.payment_term.name or '',
                )    
            
        def get_item_photo_context(self, o):
            ''' Update context for load particular photo
            '''
            order_pool = self.pool.get('sale.order')
            cr = self.cr
            uid  = self.uid
            context = {'album_code': 'QUOTATION', }
            
            return order_pool.browse(cr, uid, o.id, context=context).order_line
                    
        def get_total_volume(self, order_line):
            ''' Function that compute total volume for 1 or more items
            '''
            total = 0.0
            for item in order_line:
                product = item.product_id
                if not product.q_x_pack: 
                    continue
                    
                if product:
                    total += item.product_uom_qty * (
                        product.pack_l * product.pack_h * product.pack_p / \
                        1000000.0) / product.q_x_pack
            return '%2.2f' % total
        def total_volume(self, order_id):
            ''' calculate total volume for all items present in order
            '''
            #item_list = self.pool.get('purchase.order').browse(
            #    self.cr, self.uid, order_id).order_line
            #if item_list:
            #    return self.get_total_volume([item.id for item in item_list])
            return ''
             
        def temp_get_order(self):
            pool = self.pool.get('product.product')
            item_ids = pool.search(self.cr, self.uid, [])
            return pool.browse(self.cr, self.uid, item_ids)
            

        def clean_description(self, name):
            return name.split("]")[-1:]
        """
        def get_fabric_description(product):
            """ Return correct description depend on code
                (write only for TS TL MS TS PO
            """
            if not product:
                return ''
            default_code = product.default_code
            if default_code[:2].upper() in ('TL', 'TS', 'MT', 'MS', 'PO'):
                return u' %s' % (product.fabric or '')
            return ''

        def try_int(value):
            """ Try convert in int intead return normal data
            """
            try:
                return int(value)
            except:
                return value or ''

        """    
        def get_fabric(code, language):
            ''' Return type of fabric depend on start code
            '''
            code = code.upper()
            if code[3:6] == 'TXI':
                if language == 'it_IT':
                    return 'Texfil ignifugo'
                else:    
                    return 'Texfil fire retardant'
                    
            elif code[3:6] == 'TXR' or code[3:5] == 'TX':
                if language == 'it_IT':
                    return 'Texfil'
                else:    
                    return 'Texfil'

            elif code[3:5] == 'PE':
                if language == 'it_IT':
                    return 'Poliestere'
                else:    
                    return 'Polyester'

            elif code[3:5] == 'S3':
                if language == 'it_IT':
                    return 'Triplex'
                else:    
                    return 'Triplex'
        
            elif code[3:5] == 'SB' or code[3:4] == 'S':
                if language == 'it_IT':
                    return 'Olefine'
                else:    
                    return 'Olefine'

            elif code[3:4] == 'L' or code[3:5] == 'IL':
                if language == 'it_IT':
                    return 'Acrypol'
                else:    
                    return 'Acrypol'

            else:        
                return '/'        

        """
        def get_telaio(name, lingua):
            """ Last minute function for convert name
                (not translated in product)
            """
            name = name.strip()
            if not name:
                _logger.error('Frame %s not found!' % name)
                return '/'

            # If name is originally in english translate in italian
            if name == 'STEEL':
                name = 'ACCIAIO'
            elif name == 'WOOD':
                name = 'LEGNO'
            elif name == 'WOODEN':
                name = 'LEGNO'
            elif name == 'IRON PAINTED':
                name = 'TINTO FERRO'
            elif name == 'IRON CHROMED':
                name = 'CROMATO FERRO'
            elif name == 'ANODIZED ALUMINIUM':
                name = 'ALLUMINIO ANODIZZATO'
            elif name in ('ALUMINIUM', 'ALUMINUM'):
                name = 'ALLUMINIO'
            elif name == 'IRON':
                name = 'FERRO'
            elif name == 'WALNUT':
                name = 'NOCE'

            ita2eng = {
               'ALLUMINIO': 'ALUMINIUM',
               'LEGNO': 'WOOD',
               'ACCIAIO': 'STEEL',
               'TINTO NOCE': 'PAINTED WALNUT',
               'NOCE': 'WALNUT',
               'ALLUMINIO ANODIZZATO': 'ANODIZED ALUMINIUM',
               'CROMATO FERRO': 'IRON CHROMED',
               'TINTO FERRO': 'IRON PAINTED',
               'FERRO': 'IRON',
               'ROBINIA': 'ROBINIA',
               }
            if lingua == 'it_IT':
                return name
            else:
                if name in ita2eng:
                    return ita2eng[name]
                else:
                    _logger.error('Frame %s not found in dict!' % name)
                    return '?'

        # ---------------------------------------------------------------------
        # Start procedure:
        # ---------------------------------------------------------------------
        if context is None:
            context = {}

        # Pool used:
        excel_pool = self.pool.get('excel.writer')

        o = self.browse(cr, uid, ids, context=context)[0]

        # ---------------------------------------------------------------------
        # Dictionary:
        # ---------------------------------------------------------------------
        lang_text = {
            'it_IT': {
                'subject': u'Offerta n.: %s del %s',
                'terms': u'Resa merce:',
                'payment': u'Pagamento:',

                'header_1': [
                    u'Immagine',
                    u'Codice',
                    u'Articolo',
                    u'Quantità',
                    u'',
                    u'Prezzo IVA escl',
                    u'Sc.',
                    u'',
                    u'Importo',
                    u'Telaio',
                    u'Φ tubo',
                    u'Peso imballo',
                    u'Pezzi per scatola',
                    u'Pezzi per bancale',
                    u'Pezzi per m3',
                    u'Pezzi per camion',
                    ],
                'header_2': [
                    u'Immagine',
                    u'Codice',
                    u'Articolo',
                    u'',
                    u'Prezzo IVA escl',
                    u'Telaio',
                    u'Φ tubo',
                    u'Peso imballo',
                    u'Pezzi per scatola',
                    u'Pezzi per bancale',
                    u'Pezzi per m3',
                    u'Pezzi per camion',
                    ],

                },

            'en_US': {
                'subject': u'Offer n.: %s dated %s',
                'terms': u'Delivery terms:',
                'payment': u'Payment terms:',

                'header_1': [
                    u'Imagine',
                    u'Item ref.',
                    u'Description',
                    u'Quantity',
                    u'',
                    u'Price',
                    u'Disc.',
                    u'',
                    u'Amount',
                    u'Frame',
                    u'Pipe Φ',
                    u'Weight / box',
                    u'Pcs / box',
                    u'Pcs / pallet',
                    u'Pcs / m3',
                    u'Pcs / truck',
                    ],
                'header_2': [
                    u'Imagine',
                    u'Item ref.',
                    u'Description',
                    u'',
                    u'Price',
                    u'Frame',
                    u'Pipe Φ',
                    u'Weight / box',
                    u'Pcs / box',
                    u'Pcs / pallet',
                    u'Pcs / m3',
                    u'Pcs / truck',
                    ],
                },
            }

        # Setup lang:
        lang = o.partner_id.lang or 'it_IT'
        if lang not in lang_text:  # only authorized:
            lang = 'it_IT'

        context['lang'] = lang
        context['aeroo_docs'] = True  # To load image

        o = self.browse(cr, uid, ids, context=context)[0] # reload data in lang
        company = o.company_id

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = _(u'Dettaglio offerta')
        ws = excel_pool.create_worksheet(name=ws_name)

        # ---------------------------------------------------------------------
        # Generate format used:
        # ---------------------------------------------------------------------
        excel_pool.set_format()
        f_title = excel_pool.get_format(key='title')
        f_title_center = excel_pool.get_format(key='title_center')
        f_header = excel_pool.get_format(key='header')
        f_text = excel_pool.get_format(key='text')
        f_center = excel_pool.get_format(key='text_center_all')
        f_number = excel_pool.get_format(key='number')
        f_number_center = excel_pool.get_format(key='number_center')

        # ---------------------------------------------------------------------
        # QUOTATION HEADER:
        # ---------------------------------------------------------------------
        from_col = 4
        row = 0
        # Partner name:
        excel_pool.write_xls_line(
            ws_name, row, [
                # todo Logo
                o.partner_id.name,
                ], default_format=f_title, col=from_col)

        # -----------------------------------------------------------------
        # Write company logo:
        # -----------------------------------------------------------------
        data = company.logo or False
        if data:
            excel_pool.write_image(
                ws_name, row, 0,
                # filename='/home/thebrush/logo.png',
                filename='company.png',
                data=excel_pool.clean_odoo_binary(data),
                positioning=0,
                tip='Image company',
                )

        # Partner address:
        if o.destination_partner_id:
            select_partner = o.destination_partner_id
        else:
            select_partner = o.partner_id

        row += 1
        excel_pool.write_xls_line(
            ws_name, row, [
                # TODO Logo
                o.destination_partner_id.name,
                ], default_format=f_title, col=from_col)

        row += 1
        excel_pool.write_xls_line(
            ws_name, row, [
                o.destination_partner_id.street or '',
                ], default_format=f_title, col=from_col)

        row += 1
        excel_pool.write_xls_line(
            ws_name, row, [
                u'%s %s %s' % (
                    o.destination_partner_id.zip or '',
                    o.destination_partner_id.city or '',
                    o.destination_partner_id.country_id.name or ' ')
                    if o.partner_id.street else '',
                ], default_format=f_title, col=from_col)

        # Extra info:
        row += 1
        excel_pool.write_xls_line(
            ws_name, row, [
                lang_text[lang]['terms'],
                o.return_id.text or '',
                ], default_format=f_title, col=from_col)

        row += 1
        excel_pool.write_xls_line(
            ws_name, row, [
                lang_text[lang]['payment'],
                o.payment_term.name or '',
                ], default_format=f_title, col=from_col)

        # Subject:
        row += 2
        excel_pool.write_xls_line(
            ws_name, row, [
                # todo Logo
                lang_text[lang]['subject'] % (
                    o.name,
                    o.date_order,  # todo format_lang(o.date_order),
                    ),
                u'%s\n' % (o.bank_id.information or '') if o.bank_id else '',
                ], default_format=f_title)

        # ---------------------------------------------------------------------
        # TABLE HEADER:
        # ---------------------------------------------------------------------
        row += 2
        # Setup:
        if o.quotation_model == 1:  # Short offer
            header = lang_text[lang]['header_1']
            width = [
                18, 12, 30,  # description
                8,  # Q.
                1, 10,  # Unit price
                10,  # Discount
                1, 10,  # Subtotal
                10, 10, 10, 10, 10, 10, 10]
        else:
            header = lang_text[lang]['header_2']
            width = [18, 15, 30, 1, 12, 10, 10, 10, 10, 10, 10, 10]

        # Write data:
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)
        excel_pool.column_width(ws_name, width)

        # ---------------------------------------------------------------------
        # DETAIL:
        # ---------------------------------------------------------------------
        row_height = 78
        for item in o.order_line:
            product = item.product_id

            # -----------------------------------------------------------------
            # Pre note:
            # -----------------------------------------------------------------
            if item.text_note_pre:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [item.text_note_pre], default_format=f_text)

            # -----------------------------------------------------------------
            # Line depend on model:
            # -----------------------------------------------------------------
            symbol = o.partner_id.property_product_pricelist.currency_id.symbol
            code = product.code or u''
            line = [
                '',  # photo place
                code,
                (u'%s%s\n%s' % (
                    item.name if item.use_text_description else \
                    item.product_id.name,
                    get_fabric_description(item.product_id),
                    item.note or '',
                    ), f_text),

                symbol,
                (item.price_subtotal, f_number_center),
                get_telaio(item.product_id.telaio or '', lang),
                try_int(item.product_id.pipe_diameter_sale),
                try_int(item.product_id.weight_packaging),
                try_int(item.product_id.item_per_box),
                try_int(item.product_id.item_per_pallet),
                try_int(item.product_id.item_per_mq),
                try_int(item.product_id.item_per_camion),
                ]

            if o.quotation_model == 1: # Detail offer:
                line = line[:3] + [
                    # Extra:
                    (try_int(item.product_uom_qty), f_number_center),

                    symbol,
                    (item.price_unit, f_number_center),

                    item.multi_discount_rates or '/',

                    ] + line[3:]

            row += 1
            excel_pool.row_height(ws_name, [row], height=row_height)
            excel_pool.write_xls_line(
                ws_name, row, line, default_format=f_center)

            # -----------------------------------------------------------------
            # Write photo: (after)
            # -----------------------------------------------------------------
            if item.insert_photo:
                data = item.product_id.default_photo or False
                if data:
                    excel_pool.write_image(
                        ws_name, row, 0,
                        filename=u'%s.png' % code,
                        x_offset=4, y_offset=4,
                        x_scale=0.33, y_scale=0.33,
                        # tip=u'Image %s' % code,
                        data=excel_pool.clean_odoo_binary(data),
                        )

            # -----------------------------------------------------------------
            # Pre note:
            # -----------------------------------------------------------------
            if item.text_note_post:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [item.text_note_post], default_format=f_text)

        # ---------------------------------------------------------------------
        # QUOTATION FOOTER:
        # ---------------------------------------------------------------------
        from_col = 4  # can be different
        row += 2
        # Company info:
        excel_pool.write_xls_line(
            ws_name, row, [
                u'%s %s - %s %s (%s) %s T. %s F. %s - %s' % (
                    company.name or '',
                    company.street or '',
                    company.zip or '',
                    company.city or '',
                    company.state_id.code or '',
                    company.country_id.name or '',
                    company.phone or '',
                    company.fax or '',
                    company.email or '',
                    )], default_format=f_title_center, col=from_col)

        row += 1

        # Company info:
        excel_pool.write_xls_line(
            ws_name, row, [
                u'C.F. - P. IVA e Reg. Imp  %s - R.E.A. n. %s - Cod. Mecc. %s - Cap. Soc. € %s>' % (
                    company.vat or '',
                    company.header_rea or '',
                    company.header_mecc or '',
                    int(company.header_capital or 0.0),
                    )
                ], default_format=f_title_center, col=from_col)

        return excel_pool.return_attachment(
            cr, uid, u'Offerta', context=context)

    # Override fake wizard button event for print this report:
    def print_quotation(self, cr, uid, ids, context=None):
        """ Override originaL function that prints the sales order and mark it
            as sent, so that we can see more easily the next step of the
            workflow
        """
        assert len(ids) == 1, \
            'This option should only be used for a single id at a time'
        self.signal_workflow(cr, uid, ids, 'quotation_sent')
        return self.pool['report'].get_action(
            cr, uid, ids, 'fiam_order_report', context=context)

    _columns = {
        'quotation_model': fields.selection([
            (1, 'Offerta dettagliata (q.-sconto-subtotali)'),
            (2, 'Offerta breve (solo q.)'),
            ], 'Model'),
        }
    _defaults = {
        'quotation_model': lambda *x: 2, # short
        }

class SaleOrderLineQuotation(orm.Model):
    _inherit='sale.order.line'

    _columns={
        'insert_photo': fields.boolean(
            'Con foto',
            help="Spuntare quando e' richiesto l'inserimento della foto "
                "a preventivo."),
        'repeat_header_line': fields.boolean(
            'Intest.',
            help="Spuntare quando e' richiesta l'intestazione, tipo dopo una "
                "riga titolo."),
        'use_amazon_description': fields.boolean(
            'Amazon description',
            help="Take amazon description instead of product's one"),
        'show_notes': fields.boolean(
            'Show notes', help='Show notes after description'),
        'note': fields.text( 'Note'),
        }

    _defaults = {
        'insert_photo': lambda *x: True,
        }

