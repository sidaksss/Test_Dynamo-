# -*- coding: utf-8 -*-
"""Prototyp: liest einen SAP-LV-Export (.xlsx) nur mit der
Python-Standardbibliothek (zipfile + xml), also ohne Zusatzinstallation
in Dynamo/CPython3. Liefert eine Liste von Zeilen als Dict
(Spaltenname -> Text) und eine Auswertung fuer die Machbarkeitsstudie.

Status: nur gegen Beispieldaten getestet, nicht in Dynamo."""

import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def _col_index(cell_ref):
	letters = re.match(r'[A-Z]+', cell_ref).group(0)
	index = 0
	for ch in letters:
		index = index * 26 + (ord(ch) - 64)
	return index - 1


def read_xlsx_rows(path):
	"""Erstes Tabellenblatt als Liste von Listen (alle Werte als Text)."""
	with zipfile.ZipFile(path) as z:
		shared = []
		if 'xl/sharedStrings.xml' in z.namelist():
			root = ET.fromstring(z.read('xl/sharedStrings.xml'))
			for si in root.findall('m:si', NS):
				shared.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
		sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
	rows = []
	for row in sheet.find('m:sheetData', NS).findall('m:row', NS):
		values = {}
		for c in row.findall('m:c', NS):
			kind = c.get('t')
			if kind == 'inlineStr':
				text = ''.join(t.text or '' for t in c.iter('{%s}t' % NS['m']))
			else:
				v = c.find('m:v', NS)
				text = v.text if v is not None and v.text is not None else ''
				if kind == 's' and text:
					text = shared[int(text)]
			values[_col_index(c.get('r'))] = text
		width = max(values) + 1 if values else 0
		rows.append([values.get(i, '') for i in range(width)])
	return rows


def read_sap_lv(path):
	rows = read_xlsx_rows(path)
	header = [h.strip() for h in rows[0]]
	records = []
	for row in rows[1:]:
		row = row + [''] * (len(header) - len(row))
		records.append(dict(zip(header, [v.strip() for v in row])))
	return records


def classify(rec):
	"""Zeilenart: TITEL/HINWEIS, MASTER, UNTERPOSITION, POSITION."""
	if rec.get('Objekttyp') == 'M':
		return 'MASTER'
	if rec.get('Objekttyp') == 'U':
		return 'UNTERPOSITION'
	if not rec.get('Leistungsnummer'):
		return 'TITEL/HINWEIS'
	return 'POSITION'


def analyse(records):
	from collections import Counter, defaultdict
	kinds = Counter(classify(r) for r in records)
	positions = [r for r in records if classify(r) in ('POSITION', 'UNTERPOSITION')]
	by_number = defaultdict(set)
	for r in positions:
		by_number[r['Leistungsnummer']].add(r['ext. Leistungsnummer'])
	products = dict((k, v) for k, v in by_number.items()
		if not re.match(r'^(FP|DL)_|^RSS-', k))
	rds_like = [r for r in records for v in r.values() if re.search(r'[+=#]\S+\.\S+', v)]
	lines = [
		'Zeilen gesamt: %d' % len(records),
		'Zeilenarten: ' + ', '.join('%s=%d' % kv for kv in sorted(kinds.items())),
		'Verschiedene Leistungsnummern: %d (davon Produkte: %d, Pauschal/Dienstleistung: %d)' % (
			len(by_number), len(products), len(by_number) - len(products)),
		'Produkte, die in mehr als einer LV-Position vorkommen: %d von %d' % (
			sum(1 for v in products.values() if len(v) > 1), len(products)),
		'Einheiten: ' + ', '.join(sorted(set(r['Basismengeneinheit'] for r in positions))),
		'Zeilen mit RDS-aehnlichem Text: %d' % len(rds_like),
		'Leistungsnummer != Materialnummer (bei Produkten): ' + ', '.join(sorted(set(
			'%s->%s' % (r['Leistungsnummer'], r['Materialnummer']) for r in positions
			if r['Leistungsnummer'] in products and r.get('Materialnummer')
			and r['Materialnummer'] != r['Leistungsnummer']))),
	]
	for number in sorted(products):
		lines.append('  %-12s -> %s' % (number, ', '.join(sorted(products[number]))))
	return '\n'.join(lines)


if __name__ == '__main__':
	print(analyse(read_sap_lv(sys.argv[1])))
