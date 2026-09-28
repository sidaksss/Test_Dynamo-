# -*- coding: utf-8 -*-
"""Dynamo Python Script node: weist den Elementtypen der gewaehlten
Kategorien ihre LV-Nummer aus einer CSV-Datenbank zu.

Ablauf:
1. Datenbank (Spalte 1 = Modell, Spalte 2 = LV-Nummer) einlesen.
   Akzeptiert ';', Tab oder ',' als Trennzeichen, ignoriert
   Anfuehrungszeichen, Kopfzeile und Leerzeilen.
2. Fenster mit allen Modellkategorien anzeigen, die Elemente enthalten;
   der Benutzer hakt die gewuenschten Kategorien an.
3. Fuer jeden Typ den Typparameter 'Modell' lesen, in der Datenbank
   nachschlagen (Gross-/Kleinschreibung und Leerzeichen egal) und die
   LV-Nummer in den Typparameter schreiben. Bereits befuellte LV-Nummern
   werden nicht ueberschrieben.
4. Alle Elemente ohne zugewiesene LV-Nummer als CSV-Fehlerliste auf dem
   Desktop ablegen.

Inputs:  IN[0] Pfad zur Datenbank-CSV
         IN[1] Name des LV-Typparameters (leer = 'LV_Nummer')
Output:  Zusammenfassung als Text.

Kompatibel mit IronPython2, CPython3 und PythonNet3 (keine f-Strings)."""

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
from RevitServices.Transactions import TransactionManager
from System.Drawing import Point, Size
from System.Windows.Forms import (Button, CheckedListBox, DialogResult,
	DockStyle, Form, FormStartPosition, Label, Panel)

doc = DocumentManager.Instance.CurrentDBDocument

database_path = IN[0]
lv_param_name = (IN[1] or '').strip() or 'LV_Nummer'

HEADER_KEYS = ('MODELL', 'MODEL', 'TYPNAME', 'TYP')
ERROR_HEADER = ['Element-ID', 'Modell', 'Kategorie', 'Familie', 'Typ', 'Grund']


# --- Datenbank ---------------------------------------------------------

def normalize(text):
	return re.sub(r'\s+', ' ', text or '').strip().upper()


def read_lines(path):
	for encoding in ('utf-8-sig', 'cp1252'):
		try:
			with io.open(path, 'r', encoding=encoding) as f:
				return f.read().splitlines()
		except UnicodeDecodeError:
			continue
	return []


def parse_database(lines):
	"""Gibt (mapping, conflicts, invalid_lines) zurueck.
	mapping:       normalisiertes Modell -> LV-Nummer
	conflicts:     normalisierte Modelle mit widerspruechlichen LV-Nummern
	invalid_lines: Zeilennummern, die nicht gelesen werden konnten"""
	mapping = {}
	conflicts = set()
	invalid_lines = []
	for number, line in enumerate(lines, 1):
		cleaned = line.replace('"', '').strip().strip(';,\t ')
		if not cleaned:
			continue
		parts = re.split(r'[;\t]', cleaned)
		if len(parts) < 2:
			parts = cleaned.split(',')
		modell = parts[0].strip()
		lv = parts[1].strip() if len(parts) > 1 else ''
		if normalize(modell) in HEADER_KEYS:
			continue
		if not modell or not lv:
			invalid_lines.append(number)
			continue
		key = normalize(modell)
		if key in mapping and mapping[key] != lv:
			conflicts.add(key)
		mapping.setdefault(key, lv)
	return mapping, conflicts, invalid_lines


# --- Kategorieauswahl ----------------------------------------------------

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
	form.Text = 'LV-Nummern zuweisen'
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
	label.Text = 'Kategorien anhaken, deren Bauteile eine LV-Nummer bekommen sollen:'
	label.Dock = DockStyle.Top
	label.Height = 40

	# Reihenfolge wichtig: das Fill-Element zuerst hinzufuegen.
	form.Controls.Add(box)
	form.Controls.Add(buttons)
	form.Controls.Add(label)
	form.AcceptButton = ok
	form.CancelButton = cancel

	if form.ShowDialog() != DialogResult.OK:
		return None
	return [categories[int(i)] for i in box.CheckedIndices]


# --- Revit-Hilfsfunktionen -----------------------------------------------

def id_value(element_id):
	value = getattr(element_id, 'Value', None)  # Revit 2024+
	if value is None:
		value = element_id.IntegerValue
	return int(value)


def param_string(element, built_in, fallback_name=None):
	p = element.get_Parameter(built_in)
	if p is None and fallback_name:
		p = element.LookupParameter(fallback_name)
	if p is None:
		return ''
	return p.AsString() or ''


def process_type(el_type, mapping, conflicts):
	"""Gibt (status, modell, familie, typ, grund) zurueck.
	status: 'geschrieben', 'vorhanden' oder 'fehler'."""
	if el_type is None:
		return ('fehler', '', '', '', 'Typ nicht gefunden')
	modell = param_string(el_type, BuiltInParameter.ALL_MODEL_MODEL, 'Modell').strip()
	familie = param_string(el_type, BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)
	typ = param_string(el_type, BuiltInParameter.SYMBOL_NAME_PARAM)

	def result(status, reason=''):
		return (status, modell, familie, typ, reason)

	p = el_type.LookupParameter(lv_param_name)
	if p is None:
		return result('fehler', "Typparameter '" + lv_param_name + "' fehlt")
	if p.StorageType != StorageType.String:
		return result('fehler', "Parameter '" + lv_param_name + "' ist kein Text-Parameter")
	if (p.AsString() or '').strip():
		return result('vorhanden')
	if not modell:
		return result('fehler', 'Parameter Modell ist leer')
	key = normalize(modell)
	if key in conflicts:
		return result('fehler', 'Modell steht mehrfach mit unterschiedlichen LV-Nummern in der Datenbank')
	lv = mapping.get(key)
	if lv is None:
		return result('fehler', 'Modell nicht in Datenbank')
	if p.IsReadOnly:
		return result('fehler', "Parameter '" + lv_param_name + "' ist schreibgeschuetzt")
	try:
		p.Set(lv)
	except Exception as ex:
		return result('fehler', 'Schreiben fehlgeschlagen: ' + str(ex))
	return result('geschrieben')


# --- Fehlerliste -----------------------------------------------------------

def csv_field(value):
	text = '' if value is None else str(value)
	if ';' in text or '"' in text or '\n' in text:
		text = '"' + text.replace('"', '""') + '"'
	return text


def write_error_list(rows):
	desktop = System.Environment.GetFolderPath(System.Environment.SpecialFolder.Desktop)
	name = 'LV_Fehlerliste_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
	path = os.path.join(desktop, name)
	lines = [';'.join(csv_field(v) for v in row) for row in [ERROR_HEADER] + rows]
	# utf-8-sig, damit Excel Umlaute richtig anzeigt.
	with io.open(path, 'w', encoding='utf-8-sig', newline='') as f:
		f.write(u'\r\n'.join(lines) + u'\r\n')
	return path


# --- Hauptablauf -------------------------------------------------------------

def run():
	if not database_path or not os.path.isfile(database_path):
		return 'FEHLER: Datenbank-Datei nicht gefunden: ' + str(database_path)

	mapping, conflicts, invalid_lines = parse_database(read_lines(database_path))
	if not mapping:
		return 'FEHLER: In der Datenbank wurde keine gueltige Zeile gefunden.'

	selected = ask_for_categories(model_categories_with_elements(doc))
	if selected is None:
		return 'Abgebrochen. Es wurde nichts geaendert.'
	if not selected:
		return 'Keine Kategorie angehakt. Es wurde nichts geaendert.'

	type_results = {}
	error_rows = []
	element_count = 0

	TransactionManager.Instance.EnsureInTransaction(doc)
	try:
		for cat_name, cat_id, _ in selected:
			collector = FilteredElementCollector(doc).OfCategoryId(cat_id) \
				.WhereElementIsNotElementType()
			for el in collector:
				element_count += 1
				type_id = el.GetTypeId()
				if type_id is None or id_value(type_id) < 0:
					error_rows.append([id_value(el.Id), '', cat_name, '', '', 'Element hat keinen Typ'])
					continue
				key = id_value(type_id)
				if key not in type_results:
					type_results[key] = process_type(doc.GetElement(type_id), mapping, conflicts)
				status, modell, familie, typ, reason = type_results[key]
				if status == 'fehler':
					error_rows.append([id_value(el.Id), modell, cat_name, familie, typ, reason])
	finally:
		TransactionManager.Instance.TransactionTaskDone()

	statuses = [r[0] for r in type_results.values()]
	summary = [
		'FERTIG',
		'Kategorien: ' + ', '.join(c[0] for c in selected),
		'Gepruefte Elemente: ' + str(element_count),
		'Gepruefte Typen: ' + str(len(type_results)),
		'  LV-Nummer neu geschrieben: ' + str(statuses.count('geschrieben')) + ' Typen',
		'  LV-Nummer war schon vorhanden (nicht ueberschrieben): ' + str(statuses.count('vorhanden')) + ' Typen',
		'  Ohne LV-Nummer: ' + str(statuses.count('fehler')) + ' Typen',
		'Datenbank: ' + str(len(mapping)) + ' Eintraege gelesen',
	]
	if invalid_lines:
		summary.append('  Unlesbare Datenbank-Zeilen: ' + ', '.join(str(n) for n in invalid_lines))
	if conflicts:
		summary.append('  Widerspruechliche Modelle in der Datenbank: ' + ', '.join(sorted(conflicts)))
	if error_rows:
		summary.append('Fehlerliste (' + str(len(error_rows)) + ' Elemente): ' + write_error_list(error_rows))
	else:
		summary.append('Keine Fehler - alle Elemente haben eine LV-Nummer. Es wurde keine Fehlerliste erstellt.')
	return '\n'.join(summary)


OUT = run()
