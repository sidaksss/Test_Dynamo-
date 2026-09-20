# -*- coding: utf-8 -*-
"""Dynamo Python Script node 2: compares the current element records
(from node 1) against the baseline snapshot of the previous Nachtrag and
classifies every LV-Position as NEU_POSITION, MEHRUNG, MINDERUNG or
UNVERAENDERT. Also tags each element record with its Nachtrag status so
node 3 can write the shared parameters back onto the model.

A LV-Position that had zero occurrences in the baseline is a brand-new
scope item and is reported separately instead of being counted as a
Mehrung, per the thesis' Nachtrag definition: only quantity changes of an
*already existing* LV-Position are Mehrung/Minderung."""

import json

current_records = IN[0]
baseline_json_path = IN[1]
current_version_label = IN[2]
nachtrag_nummer = IN[3]

if baseline_json_path:
	with open(baseline_json_path, 'r') as f:
		baseline_records = json.load(f)
else:
	baseline_records = []

baseline_by_uid = dict((r['UniqueId'], r) for r in baseline_records)
current_by_uid = dict((r['UniqueId'], r) for r in current_records)


def sum_menge(records):
	totals = {}
	for r in records:
		key = r['LV_Positionsnummer']
		totals[key] = totals.get(key, 0.0) + r['Menge']
	return totals


baseline_totals = sum_menge(baseline_records)
current_totals = sum_menge(current_records)

all_positions = set(baseline_totals.keys()) | set(current_totals.keys())

meta_by_position = {}
for r in current_records + baseline_records:
	meta_by_position.setdefault(r['LV_Positionsnummer'], r)

position_summary = []
for pos in sorted(all_positions):
	menge_basis = baseline_totals.get(pos, 0.0)
	menge_aktuell = current_totals.get(pos, 0.0)
	delta = menge_aktuell - menge_basis

	if menge_basis == 0.0 and menge_aktuell > 0.0:
		klassifikation = 'NEU_POSITION'
	elif delta > 0.0:
		klassifikation = 'MEHRUNG'
	elif delta < 0.0:
		klassifikation = 'MINDERUNG'
	else:
		klassifikation = 'UNVERAENDERT'

	if klassifikation == 'UNVERAENDERT':
		continue

	meta = meta_by_position[pos]
	position_summary.append({
		'LV_Positionsnummer': pos,
		'LV_Kurztext': meta.get('LV_Kurztext', ''),
		'Basismengeneinheit': meta.get('Basismengeneinheit', ''),
		'Stueckzahl_Nachtrag': delta,
		'Gesamtstueckzahl_bisher': menge_aktuell,
		'Klassifikation': klassifikation,
	})

element_updates = []
for uid, rec in current_by_uid.items():
	baseline_rec = baseline_by_uid.get(uid)
	if baseline_rec is None:
		status = 'NEU_ELEMENT' if rec['LV_Positionsnummer'] not in baseline_totals else 'MEHRUNG'
		erstversion = current_version_label
	elif baseline_rec['LV_Positionsnummer'] != rec['LV_Positionsnummer']:
		status = 'AUSTAUSCH'
		erstversion = baseline_rec.get('Nachtrag_Erstversion', current_version_label)
	else:
		status = 'UNVERAENDERT'
		erstversion = baseline_rec.get('Nachtrag_Erstversion', current_version_label)

	bisheriger_nachtrag = baseline_rec.get('Nachtrag_Nummer', '') if baseline_rec else ''
	element_updates.append({
		'UniqueId': uid,
		'ElementId': rec['ElementId'],
		'Nachtrag_Status': status,
		'Nachtrag_Erstversion': erstversion,
		'Nachtrag_Nummer': nachtrag_nummer if status != 'UNVERAENDERT' else bisheriger_nachtrag,
	})

entfallene_elemente = [r for uid, r in baseline_by_uid.items() if uid not in current_by_uid]

OUT = [position_summary, element_updates, entfallene_elemente, current_records]
