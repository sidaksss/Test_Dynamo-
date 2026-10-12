# -*- coding: utf-8 -*-
"""Dynamo Python Script node: RDS-Diagnose (NUR LESEN, schreibt nichts
ins Modell).

Sammelt fuer alle Elemente der gewaehlten Kategorien Modell, RDS-Parameter,
LV-Parameter, Kategorie, Familie und Typ und gibt fuer jeden Parameter an,
ob er am Exemplar (E), am Typ (T), an beiden (E+T) oder gar nicht (-)
gefunden wurde. Ergebnis: drei CSV-Dateien in einem neuen Ordner auf dem
Desktop:
  1_Elemente.csv    eine Zeile pro Element
  2_Typen.csv       eine Zeile pro Typ: Ist das RDS-Merkmal je Typ einheitlich?
  3_Parameter.csv   eine Zeile pro Parameter: Wo liegt er, wie oft gefuellt?

Inputs:  IN[0] weitere Parameternamen, durch Komma oder Semikolon getrennt
         (leer = nur die Standardliste)
Output:  Zusammenfassung als Text.

Status: Prototyp, nur gegen ein simuliertes Modell getestet.
Kompatibel mit CPython3 und PythonNet3 (keine f-Strings)."""

import datetime
import io
import os
import re

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
import System
from Autodesk.Revit.DB import (BuiltInParameter, CategoryType,
	FilteredElementCollector, StorageType)
from RevitServices.Persistence import DocumentManager
from System.Drawing import Point, Size
from System.Windows.Forms import (Button, CheckedListBox, DialogResult,
	DockStyle, Form, FormStartPosition, Label, Panel)

doc = DocumentManager.Instance.CurrentDBDocument

# (Spaltenname, BuiltInParameter oder None, Parametername)
BUILT_IN_SPECS = [
	('Modell', BuiltInParameter.ALL_MODEL_MODEL, 'Modell'),
	('Hersteller', BuiltInParameter.ALL_MODEL_MANUFACTURER, 'Hersteller'),
	('Typkommentare', BuiltInParameter.ALL_MODEL_TYPE_COMMENTS, 'Typkommentare'),
	('Beschreibung', BuiltInParameter.ALL_MODEL_DESCRIPTION, 'Beschreibung'),
	('Kommentare', BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS, 'Kommentare'),
	('Kennzeichen', BuiltInParameter.ALL_MODEL_MARK, 'Kennzeichen'),
]
NAMED_PARAMS = [
	'RDS_Code', 'RDS_Projekt', 'RDS_Bauabschnitt', 'RDS_Modul', 'RDS_Teilmodul',
	'RDS_Gebaeude', 'RDS_Geschoss', 'RDS_Segment', 'RDS_Raum', 'RDS_System',
	'RDS_Systemkennzeichnung', 'RDS_SystemNum', 'RDS_Funktion', 'RDS_FunktionsNum',
	'ZWP_400_LV_Position', 'ZWP_400_LP8_Abrechnung', 'ZWP_400_Auswahlfilter',
	'LV_Nummer', 'LV_Positionsnummer',
]

extra = [n.strip() for n in re.split(r'[;,]', IN[0] or '') if n.strip()]
SPECS = BUILT_IN_SPECS + [(n, None, n) for n in NAMED_PARAMS + extra]
# doppelte Namen entfernen, Reihenfolge behalten
_seen = set()
SPECS = [s for s in SPECS if not (s[0] in _seen or _seen.add(s[0]))]

# ANNAHME (aus einem einzigen Beispiel abgeleitet): Aufbau des RDS_Code
# +Projekt.Modul.Teilmodul.Gebaeude.Geschoss.Segment#System.Systemkennz.SystemNum=Funktion.FunktionsNum-Produkt
RDS_PATTERN = re.compile(r'^\+(?P<ort>[^#=]*)(?:#(?P<system>[^=]*))?(?:=(?P<funktion>[^-]*))?(?:-(?P<produkt>.*))?$')


# --- Kategorieauswahl (wie in lv_mapping) ----------------------------------

def model_categories_with_elements(document):
	result = []
	for cat in document.Settings.Categories:
		if cat.CategoryType != CategoryType.Model:
			continue
		count = FilteredElementCollector(document).OfCategoryId(cat.Id) \
			.WhereElementIsNotElementType().GetElementCount()
		if count:
			result.append((cat.Name, cat.Id, count))
	result.sort(key=lambda c: c[0].lower())
	return result


def ask_for_categories(categories):
	form = Form()
	form.Text = 'RDS-Diagnose (nur lesen)'
	form.StartPosition = FormStartPosition.CenterScreen
	form.Size = Size(480, 600)
	form.TopMost = True

	box = CheckedListBox()
	box.CheckOnClick = True
	box.Dock = DockStyle.Fill
	for name, _, count in categories:
		box.Items.Add('{0}   ({1} Elemente)'.format(name, count))

	buttons = Panel()
	buttons.Dock = DockStyle.Bottom
	buttons.Height = 50
	ok = Button()
	ok.Text = 'OK'
	ok.DialogResult = DialogResult.OK
	ok.Size = Size(100, 30)
	ok.Location = Point(240, 10)
	cancel = Button()
	cancel.Text = 'Abbrechen'
	cancel.DialogResult = DialogResult.Cancel
	cancel.Size = Size(100, 30)
	cancel.Location = Point(350, 10)
	buttons.Controls.Add(ok)
	buttons.Controls.Add(cancel)

	label = Label()
	label.Text = 'Kategorien anhaken, die untersucht werden sollen (es wird nichts veraendert):'
	label.Dock = DockStyle.Top
	label.Height = 40

	form.Controls.Add(box)
	form.Controls.Add(buttons)
	form.Controls.Add(label)
	form.AcceptButton = ok
	form.CancelButton = cancel

	if form.ShowDialog() != DialogResult.OK:
		return None
	return [categories[int(i)] for i in box.CheckedIndices]


# --- Parameter lesen -----------------------------------------------------------

def id_value(element_id):
	value = getattr(element_id, 'Value', None)  # Revit 2024+
	if value is None:
		value = element_id.IntegerValue
	return int(value)


def find_param(element, built_in, name):
	"""Gibt (Parameter, Anzahl gleichnamiger Parameter) zurueck."""
	if element is None:
		return None, 0
	if built_in is not None:
		p = element.get_Parameter(built_in)
		if p is not None:
			return p, 1
	found = list(element.GetParameters(name))
	return (found[0] if found else None), len(found)


def param_text(p):
	if p is None:
		return ''
	st = p.StorageType
	if st == StorageType.String:
		return (p.AsString() or '').strip()
	if not p.HasValue:
		return ''
	if st == StorageType.Integer:
		return str(p.AsInteger())
	return (p.AsValueString() or '').strip()


def storage_name(p):
	if p is None:
		return ''
	for name in ('String', 'Integer', 'Double', 'ElementId'):
		if p.StorageType == getattr(StorageType, name):
			return name
	return 'Sonstiges'


def read_spec(el, el_type, spec):
	"""Gibt (Wert, Ort, Datentyp, mehrfach) zurueck. Ort: E, T, E+T oder -."""
	_, built_in, name = spec
	p_inst, n_inst = find_param(el, built_in, name)
	p_type, n_type = find_param(el_type, built_in, name)
	if p_inst is not None and p_type is not None:
		where = 'E+T'
	elif p_inst is not None:
		where = 'E'
	elif p_type is not None:
		where = 'T'
	else:
		where = '-'
	value = param_text(p_inst) or param_text(p_type)
	p = p_inst if p_inst is not None else p_type
	return value, where, storage_name(p), max(n_inst, n_type) > 1


def normalize(text):
	return re.sub(r'\s+', ' ', (text or '').replace('_', ' ')).strip().upper()


def rds_type_key(values):
	"""Typbezogener Kandidat-Schluessel: Systemkennzeichnung|Funktion
	(ohne Zaehlnummern und Ortsangaben). ANNAHME, siehe Studie."""
	system = normalize(values.get('RDS_Systemkennzeichnung'))
	funktion = normalize(values.get('RDS_Funktion'))
	if not system and not funktion:
		return ''
	return system + '|' + funktion


def rds_consistency(values):
	"""Stimmt RDS_Code mit den Einzelparametern ueberein? ja/nein/unbekannt."""
	code = values.get('RDS_Code', '')
	parts = ['RDS_Projekt', 'RDS_Modul', 'RDS_Teilmodul', 'RDS_Gebaeude', 'RDS_Geschoss',
		'RDS_Segment', 'RDS_System', 'RDS_Systemkennzeichnung', 'RDS_SystemNum',
		'RDS_Funktion', 'RDS_FunktionsNum']
	if not code or not all(values.get(p) for p in parts):
		return 'unbekannt'
	v = values
	expected = '+{0}.{1}.{2}.{3}.{4}.{5}#{6}.{7}.{8}={9}.{10}'.format(*[v[p] for p in parts])
	return 'ja' if code.startswith(expected) else 'nein'


# --- CSV ---------------------------------------------------------------------------

def csv_field(value):
	text = '' if value is None else str(value)
	if ';' in text or '"' in text or '\n' in text:
		text = '"' + text.replace('"', '""') + '"'
	return text


def write_csv(path, rows):
	lines = [';'.join(csv_field(v) for v in row) for row in rows]
	with io.open(path, 'w', encoding='utf-8-sig', newline='') as f:
		f.write(u'\r\n'.join(lines) + u'\r\n')


def percent(part, total):
	return '0 %' if not total else '{0:.0f} %'.format(100.0 * part / total)


# --- Hauptablauf ---------------------------------------------------------------------

def run():
	selected = ask_for_categories(model_categories_with_elements(doc))
	if selected is None:
		return 'Abgebrochen.'
	if not selected:
		return 'Keine Kategorie angehakt.'

	names = [s[0] for s in SPECS]
	element_rows = []
	types = {}
	param_stats = dict((n, {'E': 0, 'T': 0, 'E+T': 0, '-': 0, 'gefuellt': 0, 'typen': set(), 'mehrfach': 0}) for n in names)
	type_cache = {}

	for cat_name, cat_id, _ in selected:
		for el in FilteredElementCollector(doc).OfCategoryId(cat_id).WhereElementIsNotElementType():
			type_id = el.GetTypeId()
			tkey = id_value(type_id) if type_id is not None else -1
			if tkey not in type_cache:
				type_cache[tkey] = doc.GetElement(type_id) if tkey >= 0 else None
			el_type = type_cache[tkey]
			familie = typ = ''
			if el_type is not None:
				familie = param_text(el_type.get_Parameter(BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM))
				typ = param_text(el_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM))

			values = {}
			places = []
			for spec in SPECS:
				value, where, storage, multiple = read_spec(el, el_type, spec)
				values[spec[0]] = value
				places.append(where)
				stat = param_stats[spec[0]]
				stat[where] += 1
				if value:
					stat['gefuellt'] += 1
				if storage:
					stat['typen'].add(storage)
				if multiple:
					stat['mehrfach'] += 1

			match = RDS_PATTERN.match(values.get('RDS_Code', ''))
			aspects = [match.group(g) or '' for g in ('ort', 'system', 'funktion', 'produkt')] if match else ['', '', '', '']
			key = rds_type_key(values)
			element_rows.append(
				[id_value(el.Id), cat_name, familie, typ]
				+ [values[n] for n in names]
				+ ['/'.join(places)]
				+ aspects + [key, normalize(values.get('Modell')), rds_consistency(values)])

			t = types.setdefault(tkey, {'cat': cat_name, 'fam': familie, 'typ': typ, 'n': 0,
				'modell': values.get('Modell', ''), 'funktion': set(), 'system': set(),
				'keys': set(), 'mit_code': 0, 'lv': set()})
			t['n'] += 1
			if values.get('RDS_Funktion'):
				t['funktion'].add(values['RDS_Funktion'])
			if values.get('RDS_Systemkennzeichnung'):
				t['system'].add(values['RDS_Systemkennzeichnung'])
			if key:
				t['keys'].add(key)
			if values.get('RDS_Code'):
				t['mit_code'] += 1
			for lv_name in ('ZWP_400_LV_Position', 'LV_Nummer', 'LV_Positionsnummer'):
				if values.get(lv_name):
					t['lv'].add(lv_name + '=' + values[lv_name])

	folder = os.path.join(
		System.Environment.GetFolderPath(System.Environment.SpecialFolder.Desktop),
		'RDS_Diagnose_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
	os.makedirs(folder)

	write_csv(os.path.join(folder, '1_Elemente.csv'),
		[['Element-ID', 'Kategorie', 'Familie', 'Typ'] + names
		+ ['Fundort je Parameter (' + '/'.join(names) + ')',
		'RDS Ort-Aspekt (+)', 'RDS System-Aspekt (#)', 'RDS Funktions-Aspekt (=)', 'RDS Produkt-Aspekt (-)',
		'Kandidat Typschluessel RDS', 'Kandidat Typschluessel Modell', 'RDS_Code passt zu Einzelparametern']]
		+ element_rows)

	type_rows = [['Typ-ID', 'Kategorie', 'Familie', 'Typ', 'Anzahl Exemplare', 'Modell',
		'Anzahl versch. RDS_Funktion', 'Werte RDS_Funktion',
		'Anzahl versch. RDS_Systemkennzeichnung', 'Werte RDS_Systemkennzeichnung',
		'Anzahl versch. RDS-Typschluessel', 'Exemplare mit RDS_Code', 'Vorhandene LV-Werte']]
	for tkey in sorted(types):
		t = types[tkey]
		type_rows.append([tkey, t['cat'], t['fam'], t['typ'], t['n'], t['modell'],
			len(t['funktion']), ', '.join(sorted(t['funktion']))[:200],
			len(t['system']), ', '.join(sorted(t['system']))[:200],
			len(t['keys']), t['mit_code'], ', '.join(sorted(t['lv']))[:200]])
	write_csv(os.path.join(folder, '2_Typen.csv'), type_rows)

	total = len(element_rows)
	param_rows = [['Parameter', 'nur Exemplar', 'nur Typ', 'Exemplar und Typ', 'nicht gefunden',
		'gefuellt', 'Anteil gefuellt', 'Datentyp', 'mehrfach gleichnamig']]
	for n in names:
		s = param_stats[n]
		param_rows.append([n, s['E'], s['T'], s['E+T'], s['-'], s['gefuellt'], percent(s['gefuellt'], total),
			', '.join(sorted(s['typen'])), s['mehrfach']])
	write_csv(os.path.join(folder, '3_Parameter.csv'), param_rows)

	n_types = len(types)
	ohne_modell = sum(1 for t in types.values() if not t['modell'])
	mit_rds = sum(1 for r in element_rows if r[4 + names.index('RDS_Code')])
	rds_types = [t for t in types.values() if t['keys']]
	einheitlich = sum(1 for t in rds_types if len(t['keys']) == 1)
	return '\n'.join([
		'FERTIG (es wurde nichts veraendert)',
		'Kategorien: ' + ', '.join(c[0] for c in selected),
		'Elemente: ' + str(total) + ', Typen: ' + str(n_types),
		'Typen ohne Modell: ' + str(ohne_modell) + ' (' + percent(ohne_modell, n_types) + ')',
		'Elemente mit RDS_Code: ' + str(mit_rds) + ' (' + percent(mit_rds, total) + ')',
		'Typen mit RDS, deren RDS-Typschluessel ueber alle Exemplare gleich ist: '
			+ str(einheitlich) + ' von ' + str(len(rds_types)),
		'Fundort RDS_Code: ' + ', '.join(k + '=' + str(param_stats['RDS_Code'][k]) for k in ('E', 'T', 'E+T', '-')),
		'Ergebnisordner: ' + folder,
	])


OUT = run()
