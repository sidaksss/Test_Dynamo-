# -*- coding: utf-8 -*-
"""Dynamo Python Script node 4: turns the position_summary (node 2) into a
2D list [row][col] ready for the OOTB `Data.ExportExcel` node, plus a
snapshot JSON of the current state to serve as next run's baseline.

Also splits NEU_POSITION rows into their own block so the Nachtrag sheet
can visually separate genuinely new scope from Mehrung/Minderung of
existing LV-Positions, per the thesis' Nachtrag definition."""

import json

position_summary = IN[0]
nachtrag_nummer = IN[1]
erstellungsdatum = IN[2]
modellversion = IN[3]
current_records = IN[4]
snapshot_out_path = IN[5]

header = [
	'LV-Positionsnummer', 'Kurztext Leistung', 'Basismengeneinheit',
	'Stueckzahl (' + nachtrag_nummer + ')', 'Gesamtstueckzahl bisher',
	'Klassifikation',
]

meta_rows = [
	['Nachtrag', nachtrag_nummer],
	['Erstellungsdatum', erstellungsdatum],
	['Modellversion', modellversion],
	[],
]

mehrung_minderung = [r for r in position_summary if r['Klassifikation'] in ('MEHRUNG', 'MINDERUNG')]
neue_positionen = [r for r in position_summary if r['Klassifikation'] == 'NEU_POSITION']


def to_rows(records):
	rows = []
	for r in records:
		rows.append([
			r['LV_Positionsnummer'],
			r['LV_Kurztext'],
			r['Basismengeneinheit'],
			r['Stueckzahl_Nachtrag'],
			r['Gesamtstueckzahl_bisher'],
			r['Klassifikation'],
		])
	return rows


table = []
table.extend(meta_rows)
table.append(['Mehrungen / Minderungen bestehender LV-Positionen'])
table.append(header)
table.extend(to_rows(mehrung_minderung))
table.append([])
table.append(['Neue Positionen (kein Vorgaenger in Ursprungsversion)'])
table.append(header)
table.extend(to_rows(neue_positionen))

if snapshot_out_path:
	with open(snapshot_out_path, 'w') as f:
		json.dump(current_records, f)

OUT = table
