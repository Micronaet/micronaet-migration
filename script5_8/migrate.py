#!/usr/bin/python
# coding=utf-8
###############################################################################
#
#    Micronaet S.r.l., Migration script for PostgreSQL
#    Copyright (C) 2002-2013 Micronaet SRL (<http://www.micronaet.it>).
#    All Rights Reserved
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
###############################################################################
import sys
import os
import ConfigParser
from openerp.openerp import server
from openerp.objects import table
import pdb


# -----------------------------------------------------------------------------
#        Set up parameters (for connection to Open ERP Database)
# -----------------------------------------------------------------------------
config = ConfigParser.ConfigParser()

config_file = os.path.expanduser(
    os.path.join("~", "etl", "minerals", "openerp.5.cfg"))
config.read([config_file])
host5 = config.get('dbaccess', 'server')
dbname5 = config.get('dbaccess', 'dbname')
orm_user5 = config.get('dbaccess', 'user')
orm_pwd5 = config.get('dbaccess', 'pwd')
orm_port5 = config.get('dbaccess', 'port')
pg_user5 = config.get('postgres', 'user')
pg_pwd5 = config.get('postgres', 'pwd')
pg_port5 = config.get('postgres', 'port')
verbose5 = config.get('import_mode', 'verbose')

config_file = os.path.expanduser(
    os.path.join("~", "etl", "minerals", "openerp.8.cfg"))
config.read([config_file])
host7 = config.get('dbaccess', 'server')
dbname7 = config.get('dbaccess', 'dbname')
orm_user7 = config.get('dbaccess', 'user')
orm_pwd7 = config.get('dbaccess', 'pwd')
orm_port7 = config.get('dbaccess', 'port')
pg_user7 = config.get('postgres', 'user')
pg_pwd7 = config.get('postgres', 'pwd')
pg_port7 = config.get('postgres', 'port')
verbose7 = config.get('import_mode', 'verbose')

# Tables v. 50:
o5 = server(
    dbname = dbname5, host = host5, verbose = verbose5,
    orm_user = orm_user5, orm_password = orm_pwd5, orm_port = orm_port5,
    pg_user = pg_user5, pg_password = pg_pwd5, pg_port = pg_port5)

# Tables v. 80:
o8 = server(
    dbname=dbname8, host=host8, verbose=verbose8,
    orm_user=orm_user8, orm_password=orm_pwd8, orm_port=orm_port8,
    pg_user=pg_user8, pg_password=pg_pwd8, pg_port=pg_port8)

# Database dictionary for convert elements:
berkeley_tables = {}

# -----------------------------------------------------------------------------
#                                Migration tables
# -----------------------------------------------------------------------------
print "*" * 50, "\n", " " * 12, "Start Migration:\n", "*" * 50


# *************************** Usefull objects *********************************
# Object that are in linked in almost all other object
# Usually manually linked or only_create elements
# *****************************************************************************

# Operation: manually mapping
# Particularity: 1st static association
res_company = table(
    name = 'res.company',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        },
)
#res_company.migrate()

# Operation: manually mapping
res_users = table(
    name = 'res.users',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # admin
        3: 5,   # ravelli
        4: 9,   # armando
        5: 10,  # vittoriana
        5: 8,   # alberto
        },
)
#res_users.migrate()

# Operation: manually mapping
account_analytic_journal = table(
    name = 'account.analytic.journal',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # default
        },
)
#account_analytic_journal.migrate()

# Operation: manually mapping
#
# |==> account.account.template  >> on property_account_expense_categ type many2one
# |==> account.account.template  >> on property_account_expense       type many2one
# |==> account.account.template  >> on property_account_receivable    type many2one
# |==> account.account.template  >> on property_account_payable       type many2one
# |==> account.account.template  >> on property_reserve_and_surplus_account type many2one
# |==> account.tax.code.template >> on tax_code_root_id               type many2one
# |==> account.account.template  >> on property_account_income_categ  type many2one
# |==> account.account.template  >> on property_account_income        type many2one
# |==> account.account.template  >> on bank_account_view_id           type many2one
# |==> account.account.template  >> on account_root_id                type many2one
#
# |  > (account.tax.template     >> on tax_template_ids               type one2many)
account_chart_template = table(
    name = 'account.chart.template',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 2,   # Italian Chart
        },
)
#account_chart_template.migrate()

# Operation: mapping ID
#
# |==> stock.location                 >> on lot_output_id             type many2one       
# |==> stock.location                 >> on lot_stock_id              type many2one       
# |==> res.partner.address            >> on partner_address_id        type many2one       
# |==> res.company                    >> on company_id                type many2one       
# |==> stock.location                 >> on lot_input_id              type many2one       
stock_warehouse = table(
    name = 'stock.warehouse',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Company
        },
)
#stock_warehouse.migrate()

# Operation: manually mapping
account_fiscal_position = table(
    name = 'account.fiscal.position',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Italian
        2: 2,   # Extra CEE
        3: 3,   # Intra CEE
        },
)
#account_fiscal_position.migrate()

# Operation: manually mapping
# |==> account.chart.template         >> on chart_template_id         type many2one
#
# |  > (account.fiscal.position.tax.template >> on tax_ids            type one2many)
# |  > (account.fiscal.position.account.template >> on account_ids    type one2many)
account_fiscal_position_template = table(
    name = 'account.fiscal.position.template',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 3,   # Italian
        2: 4,   # Extra CEE
        3: 5,   # Intra CEE
        },
)
#account_fiscal_position_template.migrate()

# Operation: association ID (simple obj)
# Particularity: manual mapping for no key
#
account_account_type = table(
    name = 'account.account.type',
    key = 'code', # not true!! (see asset)
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 2,   # reveivable
        2: 3,   # payable
        3: 1,   # view
        4: 8,   # income
        5: 9,   # expense
        6: 14,  # tax
        7: 5,   # cash
        8: 6,   # asset
        9: 4,   # bank
        10: 15, # equity
    },
)
#account_account_type.migrate()

# Operation: manually mapping
#
# |  > (account.payment.term.line  >> on line_ids  type one2many)
account_payment_term = table(
    name = 'account.payment.term',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 3,   # Default
        },
)
#account_payment_term.migrate()

# Operation: manually mapping
# |==> res.currency                   >> on currency_id               type many2one
product_price_type = table(
    name = 'product.price.type',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        2: 2,
        },
)
#product_price_type.migrate()

# Operation: manually mapping
# |==> res.company                    >> on company_id                type many2one
# |==> res.currency                   >> on currency_id               type many2one
#
# |  > (product.pricelist.version     >> on version_id                type one2many
product_pricelist = table(
    name = 'product.pricelist',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        2: 2,
        },
)
#product_pricelist.migrate()

# Operation: manually mapping
product_pricelist_type = table(
    name = 'product.pricelist.type',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        2: 2,
        },
)
#product_pricelist_type.migrate()

# Operation: manually mapping
product_pricelist_version = table(
    name = 'product.pricelist.version',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        2: 2,
        },
)
#product_pricelist_version.migrate()

# Operation: map and create
decimal_precision = table(
    name = 'decimal.precision',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    manual_mapping = {
        3: 3,   # Account
        4: 4,   # Stock Weight
        5: 5,   # Product UoM
        6: 8,   # Shipping Delay
    },
    command = ['create'], # create only not mapped
)
#decimal_precision.migrate()

# Operation: map manually
document_directory_content_type = table(
    name = 'document.directory.content.type',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # PDF
    },
)
#document_directory_content_type.migrate()

# Operation: only create (simple obj)
product_uom_categ = table(
    name = 'product.uom.categ',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # create and update (automatic link)
)
#product_uom_categ.migrate()

# Operation: only create 
# |==> product.uom.categ    >> on category_id  type many2one       
product_uom = table(
    name = 'product.uom',
    key = 'name',
    o5 = o5,
    o8 = o8,
    manual_mapping = {
        1: 1,   # Unit
        2: 3,   # Kg
        3: 4,   # g
        4: 5,   # Hours
        5: 6,   # Day
        6: 7,   # t
        7: 8,   # m
        8: 9,   # km
        9: 10,  # cm
        11: 11, # LT         
    },
    mapping_databases = berkeley_tables,
    command = ['create'], # create and update (automatic link)
)
#product_uom.migrate()

# Operation: manually mapping
report_mimetypes = table(
    name = 'report.mimetypes',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        },
)
#report_mimetypes.migrate()

# Operation: only create (simple obj)
res_country = table(
    name = 'res.country',
    key = 'code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # create and update (automatic link)
)
#res_country.migrate()

# Operation: only create (simple obj)
res_country_state = table(
    name = 'res.country.state',
    key = 'code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # create and update (automatic link)
)
#res_country_state.migrate()

# Operation: manually mapping
# |==> res.country                    >> on country                   type many2one
# |==> res.country.state              >> on state                     type many2one
res_bank = table(
    name = 'res.bank',
    key = 'name',
    o5 = o5,
    o8 = o8,
    field_mapping = {},
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        },
    #command = [], # manually mapping, so nothing
)
#res_bank.migrate()

# Operation: manually mapping
res_lang = table(
    name = 'res.lang',
    key = 'name',
    o5 = o5,
    o8 = o8,
    field_mapping = {},
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Italian
        2: 2,   # English
        },
)
#res_lang.migrate()

# Operation: manually mapping
res_partner_title = table(
    name = 'res.partner.title',
    key = 'name',
    o5 = o5,
    o8 = o8,
    field_mapping = {},
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Corp.
        2: 2,   # Ltd
        3: 3,   # Madam
        4: 4,   # Miss
        5: 5,   # Sir
        },
    #command = [], # manually mapping, so nothing
)
#res_partner_title.migrate()

# Operation: manually mapping
stock_incoterms = table(
    name = 'stock.incoterms',
    key = 'name',
    o5 = o5,
    o8 = o8,
    field_mapping = {},
    mapping_databases = berkeley_tables,
    static = {
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7,
        8: 8,
        9: 9,
        10: 10,
        11: 11,
        12: 12,
        13: 13,
        14: 14,
        15: 15,
        },
)
#stock_incoterms.migrate()

# Operation: manually mapping
stock_journal = table(
    name = 'stock.journal',
    key = 'name',
    o5 = o5,
    o8 = o8,
    field_mapping = {},
    mapping_databases = berkeley_tables,
    static = {
        1: 1,
        },
)
#stock_journal.migrate()

# Operation: Migrate
#|==> res.company                    >> on company_id                type many2one       
#|==> stock.warehouse                >> on warehouse_id              type many2one       
#|==> product.pricelist              >> on pricelist_id              type many2one       
#|==> account.analytic.account       >> on project_id                type many2one       
#|==> account.payment.term           >> on payment_default_id        type many2one       
sale_shop = table(
    name = 'sale.shop',
    key = 'name',
    o5 = o5,
    o8 = o8,
    static = {
        1: 1,
    },
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#sale_shop.migrate()

# Operation: Mapping ID
#|==> res.partner.address >> on address_id                type many2one       
#|==> res.company         >> on chained_company_id        type many2one       
#|==> account.account     >> on valuation_in_account_id   type many2one       
#|==> stock.location      >> on location_id               type many2one       
#|==> stock.location      >> on chained_location_id       type many2one       
#|==> stock.journal       >> on chained_journal_id        type many2one       
#|==> res.company         >> on company_id                type many2one       
#|==> account.account     >> on valuation_out_account_id  type many2one       
#
#|  > (stock.location     >> on child_ids                 type one2many)
stock_location = table(
    name = 'stock.location',
    key = 'name',
    o5 = o5,
    o8 = o8,
    static = {
        1: 1,   # Physical Locations
        2: 2,   # Partner Locations
        3: 3,   # Virtual Locations
        4: 4,   # Scrapped
        5: 5,   # Inventory loss
        6: 6,   # Procurements
        7: 7,   # Production
        8: 8,   # Suppliers
        9: 9,   # Customers
        10: 10, # Company
        11: 11, # Output
        12: 12, # Stock
    },
    mapping_databases = berkeley_tables,
)
#stock_location.migrate()

# *************************** 0 relation **************************************
# Basic object without relations
# Create first for no problem in object that linked
# *****************************************************************************

# Operation: Only create
# Particularity: 1st importation with association key (no static mapping)
#                1st remove field list passed
# |==> account.journal.period >> on end_journal_period_id type many2one
# |==> res.company            >> on company_id            type many2one
#
# |  > (account.period        >> on period_ids            type one2many)
account_fiscalyear = table(
    name = 'account.fiscalyear',
    key = 'code',
    o5 = o5,
    o8 = o8,
    remove_field = ['end_journal_period_id'], # empty field (m2o recursive)
    mapping_databases = berkeley_tables,
    command = ['create'], # only create (no update) (automatic link)
)
#account_fiscalyear.migrate()

# Operation: manually mapping
oo_config = table(
    name = 'oo.config',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    static = {
        1: 1,   # Default
        },
)
#oo_config.migrate()

# Operation: only create (simple obj)
chemical_element = table(
    name = 'chemical.element',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create', 'update'], # create and update (automatic link)
)
#chemical_element.migrate()

# *************************** 1 relation **************************************
# Object that are in linked with onty 1 other object
# Created after that object (maybe it's not a 0 relation so remember priority
# *****************************************************************************


#Operation: association ID (1 relation obj)
# |==> res.company                  >> on company_id type many2one
#
# |  > (account.sequence.fiscalyear >> on fiscal_ids type one2many)
ir_sequence = table(
    name = 'ir.sequence',
    key = 'name',
    o5 = o5,
    o8 = o8,
    static = {
        #6: ,   #   Account Journal 
        7: 22,  #   Sale Journal
        9: 23,  #   Purchase Journal
        31: 24, #   Sale refund Journal
        32: 25, #   Purchase refund Journal
        #33: ,  #   Bank Journal Current
        #34: ,  #   Bank Jornal Deposit
        #35: ,  #   Bank Journal Cash
    },
    mapping_databases = berkeley_tables,
    #command = ['link'], # only link (no create or update)
)
#ir_sequence.migrate() #>>>>>>>>>> problema da risolvere per mancanza di key!

# Operation: association ID (1 relation obj)
# |==> res.company        >> on company_id type many2one
#
# |  > (res.currency.rate >> on rate_ids   type one2many)
res_currency = table(
    name = 'res.currency',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # only create (no update) (automatic link) # TODO maybe only link
)
#res_currency.migrate()

# Operation: association ID (1 relation obj)
# Particularity: 1st association ID with key = many2one
#
# |==> res.currency >> on currency_id type many2one
res_currency_rate = table(
    name = 'res.currency.rate',
    key = 'currency_id',      # particularity: key-many2one
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # only create (no update) (automatic link)
)
#res_currency_rate.migrate()

# Operation: Only create (1 relation obj)
# (|==> chemical.product.category.type  >> on type_id  type many2one)  <<< NON ESISTE PIU' !
#
# |  > (chemical.product.category.line >> on line_ids type one2many)
chemical_product_category = table(
    name = 'chemical.product.category',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create',], # create (automatic link)
)
#chemical_product_category.migrate()

# Operation: creation migration (1 relation obj)
#|  > (product.product.analysis.line >> on analysis_line_ids    type one2many)
#
#|==> chemical.product.category      >> on chemical_category_id type many2one       
product_product_analysis_model = table(
    name = 'product.product.analysis.model',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create',], # create (automatic link)
)
#product_product_analysis_model.migrate()

# Operation: creation migration (2 rel obj)
# Particularty: Double many2one key
#
# |==> product.product.analysis.model >> on model_id  type many2one       
# |==> chemical.element               >> on name      type many2one       
product_product_analysis_line = table(
    name = 'product.product.analysis.line',
    key = ['model_id', 'name'],
    o5 = o5,
    o8 = o8,
    #remove_field = ['product_id'],
    mapping_databases = berkeley_tables,
    command = ['create', 'source_order_as_is', ],   # create (automatic link)
)
#product_product_analysis_line.migrate()

# *************************** Complex relation ********************************
# Object that are in linked with more than 1 other object
# Created after that object (maybe it's not a 0 relation so remember priority
# *****************************************************************************

# Operation: association with multiple key
# Particularity: 1st: manual mapping, multiple key, only field, field mapping
#
# |==> account.fiscal.position  >> on property_account_position   type many2one
# |==> stock.location           >> on property_stock_customer     type many2one
# |==> account.account          >> on property_account_receivable type many2one
# |==> product.pricelist        >> on property_product_pricelist  type many2one
# |==> res.users                >> on user_id                     type many2one
# |==> res.partner.title        >> on title                       type many2one
# |==> res.company              >> on company_id                  type many2one
# |==> account.account          >> on property_account_payable    type many2one
# |==> res.partner              >> on parent_id                   type many2one
# |==> stock.location           >> on property_stock_supplier     type many2one
# |==> product.pricelist        >> on property_product_pricelist_purchase type many2one
# |==> res.country              >> on country                     type many2one
# |==> account.payment.term     >> on property_payment_term       type many2one
#
# |--> res.partner.category      >> on category_id                type many2many ????
#
# |  > (res.company              >> on ref_companies              type one2many)
# |  > (res.partner.event        >> on events                     type one2many)
# |  > (res.partner.bank         >> on bank_ids                   type one2many)
# |  > (res.partner              >> on child_ids                  type one2many)
# |  > (res.partner.address      >> on address                    type one2many)
# |  > (account.invoice.line     >> on invoice_ids                type one2many)
# |  > (account.analytic.account >> on contract_ids               type one2many)
res_partner = table(
    name = 'res.partner',
    key = ['mexal_c', 'mexal_s',],   # Multiple key  # TODO only name ?
    o5 = o5,
    o8 = o8,
    field_mapping = {'import': 'imported', },
    only_field = [
        'active', 'date', 'lang', 'customer', 'supplier', 'user_id', 'name',
        'company_id', 'website', 'ref', 'vat',
        'is_laboratory', 'combine_name', 'combine_name_internal', 'vat_subjected',
    ],
    mapping_databases = berkeley_tables,
    manual_mapping = {
        1:1,                         # Company record
    },
    command = [
        'create',              # Create new record not present
        'update',              # Update field in record yet present (lab, codes)
        'force_update_first',  # There's some case that key search >1 values
    ],
)
#res_partner.migrate()

# Operation: Merge data in res.partner (only update)
# Particularty: 1st: mapping of object, only update, remap key field
#
# |==> res.partner                    >> on partner_id                type many2one
# |==> res.partner.title              >> on title                     type many2one
# |==> res.country                    >> on country_id                type many2one
# |==> res.company                    >> on company_id                type many2one
# |==> res.country.state              >> on state_id                  type many2one
res_partner_address = table(
    name = 'res.partner.address',
    name_new = 'res.partner',               # Table/Object mapping
    key = 'partner_id',
    o5 = o5,
    o8 = o8,
    field_mapping = {'partner_id': 'id', }, # Remap key field
    only_field = [
        'fax', 'street2', 'phone', 'street', 'city', 'zip', 'email',  'mobile',
        'country_id', 'birthdate', 'state_id', 'email', 'type', ],
    mapping_databases = berkeley_tables,
    command = ['update', ],                 # Only Update
)
#res_partner_address.migrate()

# Operation: association ID (record all present (no constraints and no creation)
# Particularty: # 1st parent_id problems (recursive object)
#
# |==> account.account.type >> on user_type           type many2one
# |==> res.currency         >> on company_currency_id type many2one
# |==> res.company          >> on company_id          type many2one
# |==> account.account      >> on parent_id           type many2one
# |==> res.currency         >> on currency_id         type many2one
#
# |--> account.account      >> on child_id            type many2many  ***  forse già compilato
# |--> account.account      >> on child_consol_ids    type many2many  ***  forse già compilato
# |--> account.tax          >> on tax_ids             type many2many  ***  forse già compilato
#
# |  > (account.account     >> on child_parent_ids    type one2many )
account_account = table(
    name = 'account.account',
    key = 'code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['link'], # only link with existent item (automatic link) # TODO error if not present
)
#account_account.migrate()

# Operation: association ID
#
# |==> account.account                >> on default_debit_account_id  type many2one
# |==> res.users                      >> on user_id                   type many2one
# |==> res.currency                   >> on currency                  type many2one
# |==> account.analytic.journal       >> on analytic_journal_id       type many2one
# |==> account.account                >> on default_credit_account_id type many2one
# |==> res.company                    >> on company_id                type many2one
# |==> ir.sequence                    >> on sequence_id               type many2one
# |==> account.journal.view           >> on view_id                   type many2one
#
# |--> account.account                >> on account_control_ids       type many2many  *** forse già compilato
# |--> account.account.type           >> on type_control_ids          type many2many  *** forse già compilato
# |--> res.groups                     >> on groups_id                 type many2many  *** ???
account_journal = table(
    name = 'account.journal',
    key = 'code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    #command = ['create'], # only create (no update) (automatic link) (BNK3 new) # TODO << better create but raise error with BNK3
)
#account_journal.migrate()
# Per problema dovuto a ir.sequence è stato deciso ci linkare e non creare (BNK3 non esisterà)

# Operation: association ID
# Particularty: Crea tutti i periodi 2012, TODO manca però un record speciale (serve?)
#
# |==> res.company        >> on company_id                type many2one
# |==> account.fiscalyear >> on fiscalyear_id             type many2one
account_period = table(
    name = 'account.period',
    key = 'code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # only create (no update) (automatic link)
)
#account_period.migrate()

# Operation: Migration
#
# |==> res.partner.address >> on address_id       type many2one
# |==> res.partner         >> on partner_id       type many2one
# |  > (stock.move         >> on move_lines       type one2many)
# |==> purchase.order      >> on purchase_id      type many2one
# |==> stock.location      >> on location_id      type many2one
# |==> sale.order          >> on sale_id          type many2one
# |==> res.company         >> on company_id       type many2one
# |==> stock.picking       >> on backorder_id     type many2one
# |==> stock.journal       >> on stock_journal_id type many2one
# |==> stock.location      >> on location_dest_id type many2one
stock_picking = table(
    name = 'stock.picking',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'], # only create (no update) (automatic link)
)
#stock_picking.migrate()

# TODO Attenzione: product_template di fatto non si passa perchè i prodotti
# nella 7 hanno già creato il template e i prodotti di fatto vengono solo linkati
#
# Operation: Migration
#
#|==> stock.location        >> on property_stock_procurement    type many2one
#|==> product.uom           >> on uos_id                        type many2one
#|==> product.uom           >> on uom_id                        type many2one
#|==> account.account       >> on property_account_income       type many2one
#|==> product.category      >> on categ_id                      type many2one
#|==> res.users             >> on product_manager               type many2one
#|==> res.company           >> on company_id                    type many2one
#|==> product.uom           >> on uom_po_id                     type many2one
#|==> account.account       >> on property_stock_account_input  type many2one
#|==> stock.location        >> on property_stock_production     type many2one
#|==> stock.location        >> on property_stock_inventory      type many2one
#|==> res.partner           >> on seller_id                     type many2one
#|==> account.account       >> on property_stock_account_output type many2one
#|==> account.account       >> on property_account_expense      type many2one
#
#|--> account.tax           >> on supplier_taxes_id             type many2many  *** saltato questo oggetto (forse già compilato)
#|--> account.tax           >> on taxes_id                      type many2many  *** saltato questo oggetto (forse già compilato)
#
#|  > (product.supplierinfo >> on seller_ids                    type one2many)
#product_template = table(
#    name = 'product.template',
#    key = 'name',
#    o5 = o5,
#    o8 = o8,
#    mapping_databases = berkeley_tables,
#    command = ['create'], # only create (no update) (automatic link)
#)
#product_template.migrate()

# Operation: Migration
#
# (|==> chemical.product.category.type   >> on category_type_id          type many2one)  <<< non esiste più!
# |==> stock.location                    >> on location_id               type many2one
# |==> product.template                  >> on product_tmpl_id           type many2one
# |==> product.pricelist                 >> on pricelist_id              type many2one
# |==> chemical.product.category         >> on chemical_category_id      type many2one
# |==> product.product.analysis.model    >> on model_id                  type many2one
#
# |  > (product.packaging                >> on packaging                 type one2many)
# |  > (mrp.bom                          >> on bom_ids                   type one2many)
# |  > (product.product.analysis.default >> on analysis_default_line_ids type one2many)
product_product = table(
    name = 'product.product',
    key = 'default_code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    only_field = ['is_coal', 'need_analysis', 'chemical_category_id', 'combine_name', 'model_id', 'coal_type', 'combine_name_description',],
    remove_field = ['product_tmpl_id'],          # Not compiled (only update product-template)
    command = ['update'],    # only update (automatic link)
)
#product_product.migrate()

# Operation: Migration
#
# |==> res.company                    >> on company_id            type many2one       
# |==> product.product                >> on product_id            type many2one       
#
# |  > (stock.move                    >> on move_ids              type one2many)
# |  > (stock.production.lot.revision >> on revisions             type one2many)
# |  > (chemical.analysis             >> on chemical_analysis_ids type one2many)
stock_production_lot = table(
    name = 'stock.production.lot',
    key = ['name', 'product_id'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#stock_production_lot.migrate()

# Operation: Migrate
#
#|==> stock.location   >> on location_id  type many2one       
stock_location_type = table(
    name = 'stock.location.type',
    key = 'location_id',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#stock_location_type.migrate()

# Operation: Migrate
# Particulartiy: recursive
#
# |==> account.account.type       >> on user_type        type many2one
# |==> res.currency               >> on currency_id      type many2one
# |==> account.account.template   >> on parent_id        type many2one <<<<
#
# |--> account.tax.template       >> on tax_ids          type many2many   *** forse già compuilato (22)
#
# |  > (account.account.template  >> on child_parent_ids type one2many)
account_account_template = table(
    name = 'account.account.template',
    key = 'code',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['link'],    # only update (automatic link)
    extra_domain = ('id','>', 24), # Jump previuos account char accounts
)
#account_account_template.migrate()
# For recursive object field: parent_id # TODO serve? : #account_account_template.migrate()

# Operation: create and link
# |==> stock.production.lot           >> on lot_id                    type many2one       
# |==> res.partner                    >> on partner_id                type many2one       
# |==> product.product                >> on product_id                type many2one       
importation_purchase_order = table(
    name = 'importation.purchase.order',
    key = 'purchase_order',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#importation_purchase_order.migrate()

# |==> stock.location                 >> on location_id               type many2one       
importation_default_location = table(
    name = 'importation.default.location',
    key = 'location_id',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#importation_default_location.migrate()

# Empty table (maybe not needed
# 
#mrp_routing = table(
#    name = 'mrp.routing',
#    key = 'code',
#    o5 = o5,
#    o8 = o8,
#    static = {0: 0},  # <<< no elements
#    mapping_databases = berkeley_tables,
#)
#mrp_routing.migrate()

# Operation: Importation
# Particularity: Recursion
#
#|==> product.uom                    >> on product_uom               type many2one       
#|==> product.uom                    >> on product_uos               type many2one       
#|==> res.company                    >> on company_id                type many2one       
#|==> product.product                >> on product_id                type many2one       
#|==> mrp.routing                    >> on routing_id                type many2one <<<<< Empty table      
#|==> mrp.bom                        >> on bom_id                    type many2one <<<<< Recursion
#
#|--> mrp.bom                        >> on child_complete_ids        type many2many *** vedere se serve <<<
#|--> mrp.property                   >> on property_ids              type many2many *** vedere se serve <<<
#
#|  > (mrp.bom                       >> on bom_lines                 type one2many      )
#|  > (mrp.bom.revision              >> on revision_ids              type one2many      )
# First pass (create bom parent): #############################################
mrp_bom_parent = table(
    name = 'mrp.bom',
    key = ['product_id', 'code'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    source_domain = ('bom_id', '=', False),
    command = ['create'],    # only update (automatic link)
)
#mrp_bom.migrate()
# Second pass (create bom parent): ############################################
mrp_bom = table(
    name = 'mrp.bom',
    key = ['product_id', 'bom_id'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    source_domain = ('bom_id', '!=', False),
    command = ['create'],    # only update (automatic link)
)
#mrp_bom.migrate() # for recursion
# TODO NOTE: Provat a creare tutto nella stessa passata ora che è ordinato per ID

# Operation: migration
# Particularty: not recursive (as it is really)
#
#|==> res.company                    >> on company_id                type many2one       
#|==> res.partner                    >> on partner_id                type many2one
#|==> stock.journal                  >> on stock_journal_id          type many2one       
#|==> stock.location                 >> on location_dest_id          type many2one       
#|==> stock.location                 >> on location_id               type many2one       
#|==> stock.picking                  >> on backorder_id              type many2one <<< non ci sono dati nella colonna
#|==> sale.order                     >> on sale_id                   type many2one <<< non ci sono dati nella colonna
#|==> purchase.order                 >> on purchase_id               type many2one <<< non ci sono dati nella colonna
#|==> res.partner.address            >> on address_id                type many2one <<< non esiste
#
#|  > (stock.move                    >> on move_lines                type one2many)
stock_picking = table(
    name = 'stock.picking',
    key = ['name', 'date'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#stock_picking.migrate()


# Operation: migration
#|==> product.uom                    >> on product_uom               type many2one       
#|==> product.uom                    >> on product_uos               type many2one       
#|==> stock.location                 >> on location_src_id           type many2one       
#|==> res.company                    >> on company_id                type many2one       
#|==> mrp.bom                        >> on bom_id                    type many2one       
#|==> product.product                >> on product_id                type many2one       
#|==> mrp.routing                    >> on routing_id                type many2one       
#|==> stock.location                 >> on location_dest_id          type many2one       
#|==> stock.picking                  >> on picking_id                type many2one  
#|==> stock.move                     >> on move_prod_id              type many2one  << campo vuoto
#
#|--> stock.move                     >> on move_lines                type many2many ****  <<< (mrp_production_move_ids??)
#|--> stock.move                     >> on move_lines2               type many2many ****  <<< forse vuota
# 
#|  > (mrp.production.product.line   >> on product_lines             type one2many)
#|  > (stock.move                    >> on move_created_ids2         type one2many)
#|  > (stock.move                    >> on move_created_ids          type one2many)
#|  > (mrp.production.workcenter.line >> on workcenter_lines         type one2many)
mrp_production = table(
    name = 'mrp.production',
    key = 'name',
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#mrp_production.migrate()

# Operation: migrate and update (for second pass)
# Particularity: 2 steps updating, order clause
#
# |==> res.partner.address            >> on address_id                type many2one  <<< non presente
# |==> product.uom                    >> on product_uom               type many2one  
# |==> product.uom                    >> on product_uos               type many2one       
# |==> res.partner                    >> on partner_id                type many2one       
# |==> sale.order.line                >> on sale_line_id              type many2one <<< non presente
# |==> res.currency                   >> on price_currency_id         type many2one <<< non presente
# |==> stock.location                 >> on location_id               type many2one       
# |==> res.company                    >> on company_id                type many2one       
# |==> product.packaging              >> on product_packaging         type many2one <<< non presente      
# |==> purchase.order.line            >> on purchase_line_id          type many2one <<< non presente     
# |==> stock.picking                  >> on backorder_id              type many2one <<< colonna inesistente?  
# |==> stock.production.lot           >> on prodlot_id                type many2one       
# |==> stock.move                     >> on move_dest_id              type many2one 108 presenti (sempre inserito prima)
# |==> stock.tracking                 >> on tracking_id               type many2one <<< non presente
# |==> product.product                >> on product_id                type many2one       
# |==> stock.location                 >> on location_dest_id          type many2one       
# |==> mrp.production                 >> on production_id             type many2one       
# |==> stock.picking                  >> on picking_id                type many2one       
#
# |--> stock.move                     >> on move_history_ids          type many2many *** <<< 
# |--> stock.move                     >> on move_history_ids2         type many2many *** <<<
# |  > (procurement.order             >> on procurements              type one2many      )
# |  > (chemical.analysis             >> on chemical_analysis_ids     type one2many      )
stock_move = table(
    name = 'stock.move',
    key = ['name', 'date', 'picking_id', 'location_id'], # calcolato con varie prove (qui va bene)
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    #source_order = 'id',
    remove_field = ['create_date'],   # prende anche questo campo (e da errore importandolo)
    command = [
        'create',               # create only records
        ##'update',              # removed because no 1 loop steps
        'update_fixed_columns', # update 4 extra columne via PG
        #'reset_berkeley',       # delete mapping file DB and recreate
    ],    # only create and update fixed columns 
)
#stock_move.migrate()
####stock_move.migrate() # 2nd pass (adjust move_dest_id   <<< TODO ordinando per ID non server

# Operation: Migration
# Particularity: 1st date key
#
# |==> chemical.product.category      >> on chemical_category_id      type many2one       
# |==> product.product.analysis.model >> on model_id                  type many2one       
# |==> stock.production.lot           >> on prodlot_id                type many2one       
# |==> res.partner                    >> on laboratory_id             type many2one       
# |==> res.partner                    >> on laboratory1_id            type many2one       
# |==> res.partner                    >> on laboratory2_id            type many2one       
# |==> res.partner                    >> on laboratory3_id            type many2one       
# |==> product.product                >> on product_id                type many2one       
# |==> stock.move                     >> on stock_move_id             type many2one       
#
# |  > (chemical.analysis.line        >> on line_ids                  type one2many)
chemical_analysis = table(
    name = 'chemical.analysis',
    key = ['prodlot_id', 'date'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#chemical_analysis.migrate()

# Operation: Migrate
# |==> chemical.element                 >> on name                         type many2one       
# |==> product.product.analysis.default >> on chemical_analysis_default_id type many2one  <<< campo vuoto
# |==> product.product.analysis.line    >> on model_line_id                type many2one
# |==> chemical.analysis                >> on chemical_analysis_id         type many2one
chemical_analysis_line = table(
    name = 'chemical.analysis.line',
    key = ['chemical_analysis_id', 'name'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#chemical_analysis_line.migrate()

# Operation: migrate
#|==> product.uom                    >> on product_uom               type many2one       
#|==> mrp.production                 >> on production_id             type many2one       
#|==> product.uom                    >> on product_uos               type many2one       
#|==> product.product                >> on product_id                type many2one   
mrp_production_product_line = table(
    name = 'mrp.production.product.line',
    key = ['production_id', 'product_id'],
    o5 = o5,
    o8 = o8,
    mapping_databases = berkeley_tables,
    command = ['create'],    # only update (automatic link)
)
#mrp_production_product_line.migrate()

# Operation: migrate
#|==> purchase.order                 >> on purchase_id               type many2one       
#|==> product.uom                    >> on product_uom               type many2one       
#|==> res.company                    >> on company_id                type many2one       
#|==> product.uom                    >> on product_uos               type many2one       
#|==> mrp.bom                        >> on bom_id                    type many2one       
#|==> stock.location                 >> on location_id               type many2one       
#|==> stock.move                     >> on move_id                   type many2one       
#|==> product.product                >> on product_id                type many2one       
#
#|--> mrp.property                   >> on property_ids              type many2many  ***
################### ERRORE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
try:
    procurement_order = table(
        name = 'procurement.order',
        #key = ['name', 'move_id'],
        key = ['name', 'date_planned'],
        o5 = o5,
        o8 = o8,
        mapping_databases = berkeley_tables,
        command = ['create'],    # only update (automatic link)
    )
    #procurement_order.migrate()
except:
    pass
    
# --------------------
# many2many migration:
# --------------------
# NOTE: Better one time only!
#mrp_production.migrate_many2many('move_lines')
#mrp_production.migrate_many2many('move_lines2')

#stock_move.migrate_many2many('move_history_ids')
#stock_move.migrate_many2many('move_history_ids2')


#sys.exit() ##########################################################################################
# Importazione più pratica da gestire:
#res_company.migrate()
#res_users.migrate()
#account_analytic_journal.migrate()
#import pdb; pdb.set_trace()
#account_chart_template.migrate()
#import pdb; pdb.set_trace()
#stock_warehouse.migrate()
#import pdb; pdb.set_trace()
#account_fiscal_position.migrate()
#import pdb; pdb.set_trace()
#account_fiscal_position_template.migrate()
#import pdb; pdb.set_trace()
#account_account_type.migrate()
#import pdb; pdb.set_trace()
#account_payment_term.migrate()
#import pdb; pdb.set_trace()
#product_price_type.migrate()
#import pdb; pdb.set_trace()
#product_pricelist.migrate()
#import pdb; pdb.set_trace()
#product_pricelist_type.migrate()
#import pdb; pdb.set_trace()
#product_pricelist_version.migrate()
#import pdb; pdb.set_trace()
#decimal_precision.migrate()
#import pdb; pdb.set_trace()
#document_directory_content_type.migrate()
#import pdb; pdb.set_trace()
#product_uom_categ.migrate()
#import pdb; pdb.set_trace()
#product_uom.migrate()
#import pdb; pdb.set_trace()
#report_mimetypes.migrate()
#import pdb; pdb.set_trace()
#res_country.migrate()
#import pdb; pdb.set_trace()
#res_country_state.migrate()
#import pdb; pdb.set_trace()
#res_bank.migrate()
#import pdb; pdb.set_trace()
#res_lang.migrate()
#import pdb; pdb.set_trace()
#res_partner_title.migrate()
#import pdb; pdb.set_trace()
#stock_incoterms.migrate()
#import pdb; pdb.set_trace()
#stock_journal.migrate()
#import pdb; pdb.set_trace()
#sale_shop.migrate()
#import pdb; pdb.set_trace()
#stock_location.migrate()
#import pdb; pdb.set_trace()
#account_fiscalyear.migrate()
#import pdb; pdb.set_trace()
#oo_config.migrate()
#import pdb; pdb.set_trace()
#chemical_element.migrate()
#import pdb; pdb.set_trace()
#ir_sequence.migrate() #>>>>>>>>>> problema da risolvere per mancanza di key!
#import pdb; pdb.set_trace()
#res_currency.migrate()
#import pdb; pdb.set_trace()
#res_currency_rate.migrate()
#import pdb; pdb.set_trace()
#chemical_product_category.migrate()
#import pdb; pdb.set_trace()
#product_product_analysis_model.migrate()          #<<<<<<<<<<<<<<<<< numero di record diversi 65 64 
#import pdb; pdb.set_trace()
#product_product_analysis_line.migrate()            #<<<<<<<<<<<<<<<<< numero di record diversi 492 230
#import pdb; pdb.set_trace()
#res_partner.migrate()
#import pdb; pdb.set_trace()
#res_partner_address.migrate()
#import pdb; pdb.set_trace()
#account_account.migrate()
#import pdb; pdb.set_trace()
#account_journal.migrate() # Per problema dovuto a ir.sequence è stato deciso ci linkare e non creare (BNK3 non esisterà)
#import pdb; pdb.set_trace()
#account_period.migrate()
#import pdb; pdb.set_trace()
#stock_picking.migrate()
######product_template.migrate()
#import pdb; pdb.set_trace()
#product_product.migrate()
#import pdb; pdb.set_trace()
#stock_production_lot.migrate()                  # <<<<<<<<<<<<<<<<<<<< 112  104
#import pdb; pdb.set_trace()
#stock_location_type.migrate()
#import pdb; pdb.set_trace()
#account_account_template.migrate()  # For recursive object field: parent_id # TODO serve? : #account_account_template.migrate()
#import pdb; pdb.set_trace()
#importation_purchase_order.migrate()
#import pdb; pdb.set_trace()
#importation_default_location.migrate()
####mrp_routing.migrate()
#import pdb; pdb.set_trace()
#mrp_bom_parent.migrate()                                # <<<<<<<<<<<<<<<<<<<<<<<< 98 a 94
#import pdb; pdb.set_trace()
#mrp_bom.migrate() # for recursion # TODO NOTE: Provat a creare tutto nella stessa passata ora che è ordinato per ID
#import pdb; pdb.set_trace()
#stock_picking.migrate()
#import pdb; pdb.set_trace()
#mrp_production.migrate()
#import pdb; pdb.set_trace()
#stock_move.migrate()
#####stock_move.migrate() # 2nd pass (adjust move_dest_id   <<< TODO ordinando per ID non server
#import pdb; pdb.set_trace()
#import pdb; pdb.set_trace()
#chemical_analysis.migrate()
#import pdb; pdb.set_trace()
#chemical_analysis_line.migrate()
#import pdb; pdb.set_trace()
#mrp_production_product_line.migrate()
#import pdb; pdb.set_trace()
#procurement_order.migrate()  # <<<<<<<<<<<<<<< da problemi

# many2many
import pdb; pdb.set_trace()
mrp_production.migrate_many2many('move_lines')
import pdb; pdb.set_trace()
mrp_production.migrate_many2many('move_lines2')
import pdb; pdb.set_trace()
stock_move.migrate_many2many('move_history_ids')
import pdb; pdb.set_trace()
stock_move.migrate_many2many('move_history_ids2')


sys.exit()
# TODO decidere se è il caso troppe relazioni: account.tax account.tax.code account.tax.code.template
# Per ora non migrate perchè interessano solo ordini, righe fattura e prodotti (per la m2m)
# Operation: migration
# |==> res.company                    >> on company_id                type many2one       
# |==> account.account                >> on account_paid_id           type many2one       
# |==> account.tax                    >> on parent_id                 type many2one       
# |==> account.tax.code               >> on ref_tax_code_id           type many2one       
# |==> account.tax.code               >> on ref_base_code_id          type many2one       
# |==> account.tax.code               >> on tax_code_id               type many2one       
# |==> account.tax.code               >> on base_code_id              type many2one       
# |==> account.account                >> on account_collected_id      type many2one       
#
# |  > (account.tax                   >> on child_ids                 type one2many      )
#account_tax = table(
#    name = 'account.tax',
#    key = 'code',
#    o5 = o5,
#    o8 = o8,
#    mapping_databases = berkeley_tables,
#    command = ['create'],    # only update (automatic link)
#)
#account_tax.migrate()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
