#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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
import sys

start = 'statistic.partner.FIA.2023'

parameter = sys.argv[1:]
if len(parameter) == 2:
    files = parameter
elif len(parameter) == 1:  # Path and use last 2:
    path = parameter[0]
    for root, folders, files in os.path.walk(path):
        files = sorted(
            [f for f in files if f.startswith(start)])[-2]
        break
else:
    print('No 2 files passed and not path passed!: %s' % (parameter, ))
    sys.exit()

compare_partner = {}
compare_document = {}
partners = {}

verbose = False
columns = 0
data_pos = -1
for fullname in files:
    counter = 0
    total = 0.0
    data_pos += 1
    for line in open(fullname, 'r'):
        counter += 1
        if counter == 1:
            if verbose:
                print('%s. salto intestazione' % counter)
            continue

        line = line.strip()
        if not line:
            if verbose:
                print('%s. colonna vuota' % counter)
            continue

        row = line.split('|')
        if not columns:
            columns = len(row)

        if len(row) != columns:
            if verbose:
                print('%s. colonne differenti' % counter)
            continue

        partner_code = row[2].strip()
        partner_name = row[1].strip()
        if partner_code not in partners:
            partners[partner_code] = partner_name

        month = row[4].strip()
        year = row[5].strip()
        season = row[6].strip()
        period = '%s-%s' % (year, month)
        document = row[7].strip()

        amount_text = row[8].strip().replace(',', '.') or '0.0'
        amount = float(amount_text)

        if season != '1':
            if verbose:
                print('%s. stagione non corrente %s' % (counter, season))
            continue

        if partner_code not in compare_partner:
            compare_partner[partner_code] = [0.0, 0.0]
            compare_document[partner_code] = {}

        if period not in compare_document[partner_code]:
            compare_document[partner_code][period] = {}

        if document not in compare_document[partner_code][period]:
            compare_document[partner_code][period][document] = [0.0, 0.0]


        compare_partner[partner_code][data_pos] += amount
        compare_document[partner_code][period][document][data_pos] += amount

        total += amount

    print('TOTALI: %s = %s' % (fullname, total))

# Create partner compare:
f_out = open('./result/gap_oc_partner.csv', 'w')
f_out.write('Codice|Nome|Da|A|Differenza|Note\n')
for partner_code in compare_partner:
    last, current = compare_partner[partner_code]
    difference = current - last
    if abs(difference) < 0.00001:
        difference = 0.0

    if difference < 0:
        error = 'Negativa'
    else:
        error = ''

    partner_name = partners[partner_code]

    f_out.write('%s|%s|%s|%s|%s|%s\n' % (
        partner_code,
        partner_name,
        str(last).replace('.', ','),
        str(current).replace('.', ','),
        str(difference).replace('.', ','),
        error,
        ))

# Create partner period document compare:
f_out = open('./result/gap_oc_document.csv', 'w')
f_out.write('Codice|Nome|Periodo|Documento|Da|A|Differenza|Note\n')
for partner_code in compare_document:
    for period in compare_document[partner_code]:
        for document in compare_document[partner_code][period]:
            last, current = compare_document[partner_code][period][document]
            difference = current - last
            if abs(difference) < 0.00001:
                difference = 0.0

            if difference < 0:
                error = 'Negativa'
            else:
                error = ''

            partner_name = partners[partner_code]
            f_out.write('%s|%s|%s|%s|%s|%s|%s|%s\n' % (
                partner_code,
                partner_name,
                period,
                document,
                str(last).replace('.', ','),
                str(current).replace('.', ','),
                str(difference).replace('.', ','),
                error,
                ))

