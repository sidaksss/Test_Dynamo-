# -*- coding: utf-8 -*-
"""Dynamo Python Script node: GA-Diagnose (NUR LESEN, schreibt nichts ins
Modell). Erweiterung von rds_mapping/prototypen/rds_diagnose.py.

Schreibt fuer die im Fenster gewaehlten Kategorien einen Ordner
GA_Diagnose_<Zeitstempel> auf den Desktop (CSV, UTF-8 mit BOM, Trennzeichen ;):
  0_Zusammenfassung.txt
  1_Kategorien.csv             a) Uebersicht und GA-Hinweise je Kategorie
  2_Kombinationen.csv          b) eindeutige Kombinationen (Eingabe fuer KI-Schritt)
  3_Parameter.csv              c) alle vorkommenden Parameter: Exemplar/Typ, gefuellt
  4_Modell_fehlt_in_DB.csv     d) Modellnamen, die in der Datenbank-CSV fehlen
  5a_LV_Positionen.csv         e) Deckung LV -> Bauteile
  5b_Bauteile_ohne_LV.csv      e) Deckung Bauteile -> LV
  5c_Mengen_je_Leistungsnummer.csv  e) Soll (LV) gegen Ist (Modell), grob
  6_Verknuepfungen.csv         f) RVT-Verknuepfungen und ihre Elemente
  7_Filter.csv                 g) Ansichtsfilter: welcher Parameter blendet aus?

Inputs:  IN[0] Datenbank-CSV (Modell;LV-Nummer), optional
         IN[1] LV-Datei aus SAP (.xlsx oder .csv), optional
         IN[2] Name des eigenen LV-Parameters (leer = 'LV_Nummer')
         IN[3] weitere Parameternamen, durch Komma getrennt, optional
Output:  Zusammenfassung als Text.

Status: Prototyp, nur gegen ein simuliertes Modell getestet. Test in echtem
Revit steht aus. Kompatibel mit CPython3 und PythonNet3 (keine f-Strings)."""

import datetime
import io
import os
import re
import time
import zipfile
import xml.etree.ElementTree as ET

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
import System
from Autodesk.Revit.DB import (BuiltInParameter, Category, CategoryType, CheckoutStatus,
	FilteredElementCollector, LabelUtils, ParameterFilterElement,
	RevitLinkInstance, StorageType, View, WorksharingUtils)
from RevitServices.Persistence import DocumentManager
from System.Drawing import Point, Size
from System.Windows.Forms import (Application, Button, CheckedListBox,
	DialogResult, DockStyle, Form, FormStartPosition, Label, Panel)

doc = DocumentManager.Instance.CurrentDBDocument


def text_input(value):
	return '' if value is None else str(value).strip()


DB_PATH = text_input(IN[0])
LV_PATH = text_input(IN[1])
OWN_LV_PARAM = text_input(IN[2]) or 'LV_Nummer'
EXTRA_PARAMS = [n.strip() for n in re.split(r'[;,]', text_input(IN[3])) if n.strip()]

ZWP_LV = 'ZWP_400_LV_Position'
ZWP_LP8 = 'ZWP_400_LP8_Abrechnung'
ZWP_FILTER = 'ZWP_400_Auswahlfilter'
RDS_NAMES = ['RDS_Code', 'RDS_Projekt', 'RDS_Bauabschnitt', 'RDS_Modul', 'RDS_Teilmodul',
	'RDS_Gebaeude', 'RDS_Geschoss', 'RDS_Segment', 'RDS_Raum', 'RDS_System',
	'RDS_Systemkennzeichnung', 'RDS_SystemNum', 'RDS_Funktion', 'RDS_FunktionsNum']

# ANNAHME: Parameternamen, die nach einer Kostengruppe aussehen.
KG_PARAM_PATTERN = re.compile(r'kostengruppe|din.?276|(^|[_ ])kg($|[_ ])', re.IGNORECASE)
# ANNAHME: Kostengruppe als dreistellige Zahl 410-499 im Familien-/Typnamen (z. B. ZWP_480_...).
KG_IN_NAME = re.compile(r'(?:^|[_ ])(4[1-9]\d)(?=[_ ]|$)')
# ANNAHME: typische Anfaenge von Siemens-GA-/Brandschutz-Produktbezeichnungen.
SIEMENS_CODE = re.compile(r'^(Q[A-Z]{2}\d|PX[A-Z0-9]|TX[A-Z]\d|DXR|POL\d|RD[A-Z]\d|RX[A-Z]\d|RAK'
	r'|G[A-Z]{2}\d|S[A-Z]{2}\d|V[A-Z]{2}\d|FD[A-Z]|FC[A-Z]?\d|FT-?\d|FA\d|UP ?\d)', re.IGNORECASE)
# ANNAHME (IEC 81346-2): Kennbuchstaben, die in der GA typisch sind:
# B messen, K verarbeiten/regeln, M antreiben, P anzeigen, Q stellen, S bedienen.
GA_FUNCTION_LETTERS = 'BKMPQS'
PROGRESS_STEP = 500


# --- kleine Hilfsfunktionen ----------------------------------------------------

def id_value(element_id):
	value = getattr(element_id, 'Value', None)  # Revit 2024+
	if value is None:
		value = element_id.IntegerValue
	return int(value)


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
	for name in ('String', 'Integer', 'Double', 'ElementId'):
		if p.StorageType == getattr(StorageType, name):
			return name
	return 'Sonstiges'


def by_name(element, name):
	if element is None:
		return None
	found = list(element.GetParameters(name))
	return found[0] if found else None


def by_builtin(element, built_in):
	if element is None:
		return None
	return element.get_Parameter(built_in)


def value_of(el, el_type, name, built_in=None):
	"""Wert eines Parameters: erst am Exemplar, dann am Typ."""
	for target in (el, el_type):
		p = by_builtin(target, built_in) if built_in is not None else None
		if p is None:
			p = by_name(target, name)
		text = param_text(p)
		if text:
			return text
	return ''


def collapse(text):
	return re.sub(r'\s+', ' ', text or '').strip().upper()


def nospace(text):
	return re.sub(r'\s+', '', text or '').upper()


def model_candidates(modell):
	"""Vergleichsschluessel fuer 'Modell': ganz, erstes Wort, erste zwei Woerter."""
	words = collapse(modell).split(' ')
	result = []
	for c in (''.join(words), words[0], ''.join(words[:2])):
		if c and c not in result:
			result.append(c)
	return result


def real_function(funktion):
	return (funktion or '').replace('_', '').strip()


def is_siemens(hersteller, familie, modell):
	return ('SIEMENS' in (hersteller or '').upper()
		or (familie or '').upper().startswith(('SI_', 'SIE_'))
		or bool(SIEMENS_CODE.match(collapse(modell))))


def percent(part, total):
	return '0 %' if not total else '{0:.0f} %'.format(100.0 * part / total)


def top(counter, n=5):
	items = sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))[:n]
	return ', '.join('{0} ({1})'.format(k, v) for k, v in items)


def csv_field(value):
	text = '' if value is None else str(value)
	if ';' in text or '"' in text or '\n' in text:
		text = '"' + text.replace('"', '""') + '"'
	return text


def write_csv(path, rows):
	lines = [';'.join(csv_field(v) for v in row) for row in rows]
	with io.open(path, 'w', encoding='utf-8-sig', newline='') as f:
		f.write(u'\r\n'.join(lines) + u'\r\n')


class Counter(dict):
	"""Minimaler Zaehler (collections.Counter ohne Abhaengigkeiten)."""
	def add(self, key, n=1):
		self[key] = self.get(key, 0) + n


# --- Kategorieauswahl und Fortschritt ------------------------------------------

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
	form.Text = 'GA-Diagnose (nur lesen)'
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


class Progress(object):
	"""Kleines Fenster mit Fortschrittstext. Faellt still weg, wenn es nicht geht."""
	def __init__(self):
		self.form = None
		self.label = None
		try:
			self.form = Form()
			self.form.Text = 'GA-Diagnose laeuft (nur lesen)'
			self.form.StartPosition = FormStartPosition.CenterScreen
			self.form.Size = Size(460, 120)
			self.form.TopMost = True
			self.label = Label()
			self.label.Dock = DockStyle.Fill
			self.form.Controls.Add(self.label)
			self.form.Show()
		except Exception:
			self.form = None

	def show(self, text):
		if self.form is None:
			return
		try:
			self.label.Text = text
			Application.DoEvents()
		except Exception:
			self.form = None

	def close(self):
		if self.form is not None:
			try:
				self.form.Close()
			except Exception:
				pass


# --- Datenbank-CSV und LV-Datei ------------------------------------------------

def read_lines(path):
	for encoding in ('utf-8-sig', 'cp1252'):
		try:
			with io.open(path, 'r', encoding=encoding) as f:
				return f.read().splitlines()
		except UnicodeDecodeError:
			continue
	return []


def read_database(path):
	"""Modell -> LV-Nummer, tolerant wie lv_mapping (;, Tab, Anfuehrungszeichen)."""
	mapping = {}
	for line in read_lines(path):
		cleaned = line.replace('"', '').strip().strip(';,\t ')
		parts = re.split(r'[;\t]', cleaned)
		if len(parts) < 2:
			parts = cleaned.split(',')
		if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
			continue
		if collapse(parts[0]) in ('MODELL', 'MODEL', 'TYPNAME', 'TYP'):
			continue
		mapping.setdefault(nospace(parts[0]), parts[1].strip())
	return mapping


def read_xlsx_rows(path):
	ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
	with zipfile.ZipFile(path) as z:
		names = z.namelist()
		shared = []
		if 'xl/sharedStrings.xml' in names:
			for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(ns + 'si'):
				shared.append(''.join(t.text or '' for t in si.iter(ns + 't')))
		sheets = sorted(n for n in names if n.startswith('xl/worksheets/sheet'))
		sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml' if 'xl/worksheets/sheet1.xml' in names else sheets[0]))
	rows = []
	for row in sheet.find(ns + 'sheetData').findall(ns + 'row'):
		values = {}
		for c in row.findall(ns + 'c'):
			letters = re.match(r'[A-Z]+', c.get('r')).group(0)
			col = 0
			for ch in letters:
				col = col * 26 + ord(ch) - 64
			kind = c.get('t')
			if kind == 'inlineStr':
				text = ''.join(t.text or '' for t in c.iter(ns + 't'))
			else:
				v = c.find(ns + 'v')
				text = v.text if v is not None and v.text is not None else ''
				if kind == 's' and text:
					text = shared[int(text)]
			values[col - 1] = text
		width = max(values) + 1 if values else 0
		rows.append([values.get(i, '') for i in range(width)])
	return rows


def unique(values):
	result = []
	for v in values:
		if v and v not in result:
			result.append(v)
	return result


def read_lv(path):
	"""LV als Liste von Dicts mit einheitlichen Schluesseln."""
	if path.lower().endswith(('.xlsx', '.xlsm')):
		rows = read_xlsx_rows(path)
	else:
		rows = [re.split(r'[;\t]', line.replace('"', '')) for line in read_lines(path) if line.strip()]
	header = [h.strip() for h in rows[0]]

	def column(*names):
		for n in names:
			for i, h in enumerate(header):
				if h.lower() == n.lower():
					return i
		return None

	cols = {
		'pos': column('ext. Leistungsnummer', 'LV-Positionsnummer', 'Positionsnummer', 'OZ', 'Position'),
		'nr': column('Leistungsnummer'),
		'lid': column('L-Identifizierer'),
		'mat': column('Materialnummer'),
		'typ': column('Objekttyp'),
		'upos': column('Unterpositionsnummer'),
		'text1': column('Kurztextzeile 1', 'Kurztext'),
		'text2': column('Kurztextzeile 2'),
		'menge': column('Menge'),
		'einheit': column('Basismengeneinheit', 'Einheit'),
	}
	positions = []
	for row in rows[1:]:
		get = lambda key: (row[cols[key]].strip() if cols[key] is not None and cols[key] < len(row) else '')
		pos = get('pos')
		if not pos:
			continue
		try:
			menge = float(get('menge').replace(',', '.') or 0)
		except ValueError:
			menge = 0.0
		positions.append({
			'pos': pos, 'typ': get('typ'), 'upos': get('upos'), 'nr': get('nr'),
			'keys': unique([nospace(get('nr')), nospace(get('lid')), nospace(get('mat'))]),
			'text': (get('text1') + ' ' + get('text2')).strip(), 'menge': menge, 'einheit': get('einheit'),
		})
	return positions


# --- Verknuepfungen und Filter -------------------------------------------------

def link_rows(selected):
	rows = []
	for link in FilteredElementCollector(doc).OfClass(RevitLinkInstance):
		link_doc = None
		try:
			link_doc = link.GetLinkDocument()
		except Exception:
			pass
		name = link.Name
		if link_doc is None:
			rows.append([name, id_value(link.Id), 'nein', '', '', ''])
			continue
		type_cache = {}
		for cat_name, cat_id, _ in selected:
			n = 0
			siemens = 0
			for el in FilteredElementCollector(link_doc).OfCategoryId(cat_id).WhereElementIsNotElementType():
				n += 1
				tid = el.GetTypeId()
				key = id_value(tid) if tid is not None else -1
				if key not in type_cache:
					t = link_doc.GetElement(tid) if key >= 0 else None
					type_cache[key] = is_siemens(
						value_of(None, t, 'Hersteller', BuiltInParameter.ALL_MODEL_MANUFACTURER),
						param_text(by_builtin(t, BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)),
						value_of(None, t, 'Modell', BuiltInParameter.ALL_MODEL_MODEL))
				if type_cache[key]:
					siemens += 1
			if n:
				rows.append([name, id_value(link.Id), 'ja', cat_name, n, siemens])
		if not any(r[0] == name and r[1] == id_value(link.Id) for r in rows):
			rows.append([name, id_value(link.Id), 'ja', '(keine Elemente der gewaehlten Kategorien)', 0, 0])
	return rows


def param_label(param_id):
	value = id_value(param_id)
	if value >= 0:
		el = doc.GetElement(param_id)
		return el.Name if el is not None else str(value)
	try:
		bip = System.Enum.ToObject(clr.GetClrType(BuiltInParameter), value)
		return LabelUtils.GetLabelFor(bip)
	except Exception:
		return 'BuiltIn ' + str(value)


def describe_rule(rule):
	inner = getattr(rule, 'GetInnerRule', None)
	if inner is not None:
		return 'NICHT(' + describe_rule(inner()) + ')'
	parts = [param_label(rule.GetRuleParameter()), rule.GetType().Name]
	evaluator = getattr(rule, 'GetEvaluator', None)
	if evaluator is not None:
		try:
			parts.append(evaluator().GetType().Name)
		except Exception:
			pass
	for attr in ('RuleString', 'RuleValue'):
		value = getattr(rule, attr, None)
		if value is not None:
			parts.append(str(value))
	return ' '.join(parts)


def describe_filter(element_filter):
	if element_filter is None:
		return ''
	rules = getattr(element_filter, 'GetRules', None)
	if rules is not None:
		return ' UND '.join(describe_rule(r) for r in rules())
	children = getattr(element_filter, 'GetFilters', None)
	if children is not None:
		word = ' ODER ' if 'Or' in element_filter.GetType().Name else ' UND '
		return word.join('(' + describe_filter(c) + ')' for c in children())
	return element_filter.GetType().Name


def filter_rows():
	usage = {}
	for view in FilteredElementCollector(doc).OfClass(View):
		try:
			if not view.AreGraphicsOverridesAllowed():
				continue
			ids = list(view.GetFilters())
		except Exception:
			continue
		for fid in ids:
			u = usage.setdefault(id_value(fid), {'n': 0, 'hidden': 0, 'views': []})
			u['n'] += 1
			if not view.GetFilterVisibility(fid):
				u['hidden'] += 1
				if len(u['views']) < 3:
					u['views'].append(('Vorlage: ' if view.IsTemplate else '') + view.Name)
	rows = []
	for pfe in FilteredElementCollector(doc).OfClass(ParameterFilterElement):
		try:
			rules = describe_filter(pfe.GetElementFilter())
		except Exception as ex:
			rules = 'nicht lesbar: ' + str(ex)
		cats = []
		for cid in pfe.GetCategories():
			try:
				cat = Category.GetCategory(doc, cid)
			except Exception:
				cat = None
			cats.append(cat.Name if cat is not None else str(id_value(cid)))
		u = usage.get(id_value(pfe.Id), {'n': 0, 'hidden': 0, 'views': []})
		rows.append([pfe.Name, ', '.join(cats)[:300], rules, u['n'], u['hidden'], ' | '.join(u['views'])])
	return rows


# --- Hauptablauf ---------------------------------------------------------------

def run():
	started = time.time()
	categories = model_categories_with_elements(doc)
	selected = ask_for_categories(categories)
	if selected is None:
		return 'Abgebrochen.'
	if not selected:
		return 'Keine Kategorie angehakt.'

	database = read_database(DB_PATH) if DB_PATH and os.path.isfile(DB_PATH) else None
	lv = read_lv(LV_PATH) if LV_PATH and os.path.isfile(LV_PATH) else None
	lv_keys = {}
	if lv:
		for p in lv:
			for k in p['keys']:
				lv_keys.setdefault(k, set()).add(p['pos'])

	def lookup(table, modell):
		for c in model_candidates(modell):
			if c in table:
				return c
		return None

	workshared = bool(getattr(doc, 'IsWorkshared', False))
	workset_names = {}
	type_cache = {}
	cat_stats = {}
	combos = {}
	params = {}
	type_params_done = set()
	model_names = {}
	own_lv_values = Counter()
	lv_matched_by_key = Counter()
	total = sum(c[2] for c in selected)
	done = 0
	progress = Progress()

	for cat_name, cat_id, _ in selected:
		cs = cat_stats.setdefault(cat_name, dict((k, 0) for k in (
			'n', 'modell', 'rds_code', 'funktion', 'kommentar', 'zwp_lv', 'lp8', 'own_lv', 'kg_param',
			'kg_name', 'siemens', 'si_family', 'siemens_code', 'ga_function', 'nested', 'demolished',
			'owned_other', 'siem_lp8', 'siem_not_lp8', 'lp8_not_siem', 'zwp_eq_own', 'zwp_ne_own',
			'in_db', 'in_lv')))
		cs['types'] = set()
		for key in ('kg_values', 'letters', 'systems', 'worksets', 'kg_params'):
			cs[key] = Counter()

		for el in FilteredElementCollector(doc).OfCategoryId(cat_id).WhereElementIsNotElementType():
			done += 1
			if done % PROGRESS_STEP == 0:
				progress.show('{0}: {1} von {2} Elementen ({3})'.format(cat_name, done, total, percent(done, total)))

			tid = el.GetTypeId()
			tkey = id_value(tid) if tid is not None else -1
			if tkey not in type_cache:
				t = doc.GetElement(tid) if tkey >= 0 else None
				type_cache[tkey] = {
					'el': t,
					'familie': param_text(by_builtin(t, BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)),
					'typ': param_text(by_builtin(t, BuiltInParameter.SYMBOL_NAME_PARAM)),
					'count': Counter(),
				}
			ti = type_cache[tkey]
			t = ti['el']
			ti['count'].add(cat_name)
			familie, typ = ti['familie'], ti['typ']

			modell = value_of(el, t, 'Modell', BuiltInParameter.ALL_MODEL_MODEL)
			hersteller = value_of(el, t, 'Hersteller', BuiltInParameter.ALL_MODEL_MANUFACTURER)
			kommentar = value_of(el, None, 'Kommentare', BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
			rds = dict((n, value_of(el, t, n)) for n in ('RDS_Code', 'RDS_Funktion', 'RDS_System', 'RDS_Systemkennzeichnung'))
			zwp_lv = value_of(el, t, ZWP_LV)
			lp8 = value_of(el, t, ZWP_LP8) == '1'
			own_lv = value_of(el, t, OWN_LV_PARAM)
			siemens = is_siemens(hersteller, familie, modell)
			funktion = real_function(rds['RDS_Funktion'])

			host = None
			try:
				host = getattr(el, 'SuperComponent', None)
			except Exception:
				host = None
			demolished = by_builtin(el, BuiltInParameter.PHASE_DEMOLISHED)
			is_demolished = demolished is not None and demolished.HasValue and id_value(demolished.AsElementId()) >= 0

			# c) alle Parameter: Exemplar je Element, Typ einmal je Typ (spaeter gewichtet)
			kg_filled = False
			for p in el.Parameters:
				name = p.Definition.Name
				info = params.setdefault(name, {'E': 0, 'T': 0, 'E_filled': 0, 'T_filled': 0,
					'storage': storage_name(p), 'shared': bool(getattr(p, 'IsShared', False)), 'cats': set()})
				info['E'] += 1
				info['cats'].add(cat_name)
				text = param_text(p)
				if text:
					info['E_filled'] += 1
					if KG_PARAM_PATTERN.search(name):
						kg_filled = True
						cs['kg_params'].add(name)
			if t is not None and tkey not in type_params_done:
				type_params_done.add(tkey)
				ti['params'] = []
				for p in t.Parameters:
					name = p.Definition.Name
					filled = bool(param_text(p))
					ti['params'].append((name, filled, storage_name(p), bool(getattr(p, 'IsShared', False))))
					if filled and KG_PARAM_PATTERN.search(name):
						ti['kg'] = name
			if ti.get('kg'):
				kg_filled = True
				cs['kg_params'].add(ti['kg'])

			# a) Kategorie-Uebersicht
			cs['n'] += 1
			cs['types'].add(tkey)
			for flag, key in ((modell, 'modell'), (rds['RDS_Code'], 'rds_code'), (funktion, 'funktion'),
					(kommentar, 'kommentar'), (zwp_lv, 'zwp_lv'), (lp8, 'lp8'), (own_lv, 'own_lv'),
					(kg_filled, 'kg_param'), (siemens, 'siemens'), (host is not None, 'nested'),
					(is_demolished, 'demolished')):
				if flag:
					cs[key] += 1
			if familie.upper().startswith(('SI_', 'SIE_')):
				cs['si_family'] += 1
			if SIEMENS_CODE.match(collapse(modell)):
				cs['siemens_code'] += 1
			if funktion and funktion[0].upper() in GA_FUNCTION_LETTERS:
				cs['ga_function'] += 1
			if funktion:
				cs['letters'].add(funktion[0].upper())
			if rds['RDS_System']:
				cs['systems'].add(rds['RDS_System'] + ' ' + rds['RDS_Systemkennzeichnung'])
			kg_match = KG_IN_NAME.search(familie + ' ' + typ)
			if kg_match:
				cs['kg_name'] += 1
				cs['kg_values'].add(kg_match.group(1))
			if siemens and lp8:
				cs['siem_lp8'] += 1
			elif siemens:
				cs['siem_not_lp8'] += 1
			elif lp8:
				cs['lp8_not_siem'] += 1
			if zwp_lv and own_lv:
				cs['zwp_eq_own' if nospace(zwp_lv) == nospace(own_lv) else 'zwp_ne_own'] += 1
			if workshared:
				try:
					wid = id_value(el.WorksetId)
					if wid not in workset_names:
						workset_names[wid] = doc.GetWorksetTable().GetWorkset(el.WorksetId).Name
					cs['worksets'].add(workset_names[wid])
					if WorksharingUtils.GetCheckoutStatus(doc, el.Id) == CheckoutStatus.OwnedByOtherUser:
						cs['owned_other'] += 1
				except Exception:
					pass

			in_db = lookup(database, modell) if database is not None and modell else None
			in_lv = lookup(lv_keys, modell) if lv is not None and modell else None
			if in_db:
				cs['in_db'] += 1
			if in_lv:
				cs['in_lv'] += 1
				if host is None and not is_demolished:
					lv_matched_by_key.add(in_lv)
			if own_lv:
				own_lv_values.add(own_lv)

			# b) Kombinationen
			key = (cat_name, familie, typ, modell, rds['RDS_Funktion'], rds['RDS_System'],
				rds['RDS_Systemkennzeichnung'], kommentar)
			c = combos.setdefault(key, {'n': 0, 'lp8': 0, 'nested': 0, 'siemens': siemens,
				'in_db': in_db, 'in_lv': in_lv, 'own_lv': Counter()})
			c['n'] += 1
			if lp8:
				c['lp8'] += 1
			if host is not None:
				c['nested'] += 1
			if own_lv:
				c['own_lv'].add(own_lv)

			# d) Modellnamen
			if modell:
				m = model_names.setdefault(collapse(modell), {'n': 0, 'types': set(), 'cats': set(), 'in_db': in_db})
				m['n'] += 1
				m['types'].add(tkey)
				m['cats'].add(cat_name)

	progress.show('Schreibe Dateien ...')

	# Typ-Parameter gewichtet mit der Anzahl Exemplare
	for tkey, ti in type_cache.items():
		n_inst = sum(ti['count'].values())
		for name, filled, storage, shared in ti.get('params', []):
			info = params.setdefault(name, {'E': 0, 'T': 0, 'E_filled': 0, 'T_filled': 0,
				'storage': storage, 'shared': shared, 'cats': set()})
			info['T'] += n_inst
			if filled:
				info['T_filled'] += n_inst
			info['cats'].update(ti['count'].keys())

	folder = os.path.join(System.Environment.GetFolderPath(System.Environment.SpecialFolder.Desktop),
		'GA_Diagnose_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
	os.makedirs(folder)

	# 1) Kategorien
	rows = [['Kategorie', 'Exemplare', 'Typen', 'Modell gefuellt', 'RDS_Code gefuellt', 'RDS_Funktion gefuellt',
		'Kommentar gefuellt', ZWP_LV + ' gefuellt', ZWP_LP8 + ' angehakt', OWN_LV_PARAM + ' gefuellt',
		'Kostengruppen-Parameter gefuellt', 'Kostengruppen-Parameter (Namen)', 'KG im Familien-/Typnamen', 'KG-Werte im Namen',
		'Hersteller Siemens / SI_-Familie / Siemens-Code (eins davon)', 'davon SI_-Familie', 'Modell mit Siemens-Code',
		'RDS-Funktion GA-typisch (B,K,M,P,Q,S)', 'RDS-Kennbuchstaben', 'RDS-Systeme (haeufigste)',
		'Siemens-typisch UND LP8', 'Siemens-typisch OHNE LP8', 'LP8 OHNE Siemens-typisch',
		'ZWP_LV = eigene LV', 'ZWP_LV <> eigene LV', 'Modell in Datenbank', 'Modell im LV',
		'verschachtelt (Unterfamilie)', 'Abbruchphase gesetzt', 'Arbeitssaetze', 'von anderen Benutzern belegt']]
	for cat_name, _, _ in selected:
		s = cat_stats[cat_name]
		n = s['n']
		pc = lambda k: '{0} ({1})'.format(s[k], percent(s[k], n))
		rows.append([cat_name, n, len(s['types']), pc('modell'), pc('rds_code'), pc('funktion'), pc('kommentar'),
			pc('zwp_lv'), pc('lp8'), pc('own_lv'), pc('kg_param'), ', '.join(sorted(s['kg_params'])),
			pc('kg_name'), top(s['kg_values']), pc('siemens'), pc('si_family'), pc('siemens_code'),
			pc('ga_function'), top(s['letters'], 8), top(s['systems']), s['siem_lp8'], s['siem_not_lp8'],
			s['lp8_not_siem'], s['zwp_eq_own'], s['zwp_ne_own'],
			pc('in_db') if database is not None else 'keine DB', pc('in_lv') if lv is not None else 'kein LV',
			pc('nested'), pc('demolished'), top(s['worksets'], 3) if workshared else 'kein Worksharing',
			s['owned_other'] if workshared else '-'])
	write_csv(os.path.join(folder, '1_Kategorien.csv'), rows)

	# 2) Kombinationen
	rows = [['Kategorie', 'Familie', 'Typ', 'Modell', 'RDS_Funktion', 'RDS_System', 'RDS_Systemkennzeichnung',
		'Kommentar', 'Anzahl Exemplare', 'davon verschachtelt', 'davon LP8 angehakt', 'Siemens-typisch',
		'Modell in Datenbank', 'Modell im LV (Leistungsnummer)', 'vorhandene eigene LV-Nummer']]
	for key in sorted(combos, key=lambda k: (k[0], k[1], k[2], k[3], k[4], k[5], k[6], k[7])):
		c = combos[key]
		rows.append(list(key) + [c['n'], c['nested'], c['lp8'], 'ja' if c['siemens'] else 'nein',
			('ja' if c['in_db'] else 'nein') if database is not None else '',
			(c['in_lv'] or 'nein') if lv is not None else '', top(c['own_lv'], 3)])
	write_csv(os.path.join(folder, '2_Kombinationen.csv'), rows)

	# 3) Parameter
	rows = [['Parameter', 'liegt am', 'Elemente mit Parameter am Exemplar', 'davon mit Wert (Ja/Nein: auch Nein)',
		'Elemente mit Parameter am Typ', 'davon mit Wert (gewichtet mit Exemplaren)', 'Datentyp', 'gemeinsam genutzt', 'Kategorien',
		'moeglicher Kostengruppen-Parameter']]
	focus = set(['Modell', 'Kommentare', ZWP_LV, ZWP_LP8, ZWP_FILTER, OWN_LV_PARAM] + RDS_NAMES + EXTRA_PARAMS)
	for name in sorted(params, key=lambda n: (n not in focus, n.lower())):
		info = params[name]
		where = 'Exemplar und Typ' if info['E'] and info['T'] else ('Exemplar' if info['E'] else 'Typ')
		rows.append([name, where, info['E'], info['E_filled'], info['T'], info['T_filled'], info['storage'],
			'ja' if info['shared'] else 'nein', ', '.join(sorted(info['cats']))[:200],
			'ja' if KG_PARAM_PATTERN.search(name) else ''])
	for name in sorted(focus - set(params)):
		rows.append([name, 'nicht gefunden', 0, 0, 0, 0, '', '', '', ''])
	write_csv(os.path.join(folder, '3_Parameter.csv'), rows)

	# 4) Modellnamen, die in der Datenbank fehlen
	rows = [['Modell', 'Anzahl Exemplare', 'Anzahl Typen', 'Kategorien', 'Status']]
	missing = 0
	if database is None:
		rows.append(['(keine Datenbank-CSV angegeben)', '', '', '', ''])
	else:
		for name in sorted(model_names, key=lambda k: -model_names[k]['n']):
			m = model_names[name]
			if m['in_db']:
				continue
			missing += 1
			rows.append([name, m['n'], len(m['types']), ', '.join(sorted(m['cats'])), 'fehlt in Datenbank'])
	write_csv(os.path.join(folder, '4_Modell_fehlt_in_DB.csv'), rows)

	# 5) LV-Deckung
	lv_summary = 'kein LV angegeben'
	if lv is not None:
		by_nr = {}
		for p in lv:
			if p['keys']:
				by_nr.setdefault(p['keys'][0], []).append(p)
		rows = [['LV-Position', 'Objekttyp', 'Unterposition', 'Leistungsnummer', 'Kurztext', 'LV-Menge', 'Einheit',
			'Bauteile mit eigener LV-Nummer = Position', 'Bauteile mit passendem Modell (alle Positionen dieser Leistungsnummer)',
			'Positionen mit gleicher Leistungsnummer', 'Bewertung']]
		ohne = 0
		for p in lv:
			if not p['nr'] and not p['typ']:
				continue  # Titel- oder Hinweiszeile
			by_own = own_lv_values.get(p['pos'], 0)
			by_model = sum(lv_matched_by_key.get(k, 0) for k in p['keys'])
			same = len(by_nr.get(p['keys'][0], [])) if p['keys'] else 0
			if re.match(r'^(FP|DL)_|^RSS-', p['nr'].upper()):
				rating = 'Pauschale/Dienstleistung (ANNAHME: nicht modelliert)'
			elif not p['nr']:
				rating = 'Masterposition (Summe der Unterpositionen)'
			elif by_own:
				rating = 'zugeordnet ueber eigene LV-Nummer'
			elif by_model and same == 1:
				rating = 'eindeutig ueber Modell'
			elif by_model:
				rating = 'Produkt vorhanden, Position mehrdeutig'
			else:
				rating = 'keine Bauteile gefunden'
				ohne += 1
			rows.append([p['pos'], p['typ'], p['upos'], p['nr'], p['text'], p['menge'], p['einheit'],
				by_own, by_model, same, rating])
		write_csv(os.path.join(folder, '5a_LV_Positionen.csv'), rows)

		rows = [['Kategorie', 'Familie', 'Typ', 'Modell', 'Anzahl Exemplare', 'Siemens-typisch', 'Grund']]
		ohne_bt = 0
		for key in sorted(combos):
			c = combos[key]
			if c['in_lv'] or c['own_lv']:
				continue
			ohne_bt += c['n']
			rows.append([key[0], key[1], key[2], key[3], c['n'], 'ja' if c['siemens'] else 'nein',
				'Modell leer' if not key[3] else 'Modell nicht im LV'])
		write_csv(os.path.join(folder, '5b_Bauteile_ohne_LV.csv'), rows)

		rows = [['Leistungsnummer', 'Kurztext', 'LV-Menge (Summe aller Positionen)', 'Einheit', 'Anzahl LV-Positionen',
			'Bauteile im Modell (ohne verschachtelte und abgebrochene)', 'Differenz Modell - LV']]
		for nr_key in sorted(by_nr):
			ps = by_nr[nr_key]
			if re.match(r'^(FP|DL)_|^RSS-', ps[0]['nr'].upper()):
				continue
			soll = sum(p['menge'] for p in ps if p['typ'] != 'M')
			ist = sum(lv_matched_by_key.get(k, 0) for k in ps[0]['keys'])
			rows.append([ps[0]['nr'], ps[0]['text'], soll, ps[0]['einheit'], len(ps), ist, ist - soll])
		write_csv(os.path.join(folder, '5c_Mengen_je_Leistungsnummer.csv'), rows)
		lv_summary = 'LV: {0} Zeilen; Positionen ohne Bauteile: {1}; Bauteile ohne LV: {2}'.format(len(lv), ohne, ohne_bt)

	# 6) Verknuepfungen
	progress.show('Pruefe Verknuepfungen ...')
	try:
		links = link_rows(selected)
	except Exception as ex:
		links = [['Fehler beim Lesen der Verknuepfungen: ' + str(ex), '', '', '', '', '']]
	write_csv(os.path.join(folder, '6_Verknuepfungen.csv'),
		[['Verknuepfung', 'Instanz-ID', 'geladen', 'Kategorie', 'Elemente', 'davon Siemens-typisch']] + links)

	# 7) Filter
	progress.show('Pruefe Ansichtsfilter ...')
	try:
		filters = filter_rows()
	except Exception as ex:
		filters = [['Fehler beim Lesen der Filter: ' + str(ex), '', '', '', '', '']]
	write_csv(os.path.join(folder, '7_Filter.csv'),
		[['Filtername', 'Kategorien', 'Regeln (Parameter Regeltyp Vergleich Wert)', 'verwendet in Ansichten/Vorlagen',
		'davon ausgeblendet', 'Beispiele (ausgeblendet)']] + filters)
	progress.close()

	n_all = sum(s['n'] for s in cat_stats.values())
	n_links_loaded = len(set((r[0], r[1]) for r in links if r[2] == 'ja'))
	n_links = len(set((r[0], r[1]) for r in links if r[2] in ('ja', 'nein')))
	summary = [
		'FERTIG (es wurde nichts veraendert) - Dauer: {0:.0f} s'.format(time.time() - started),
		'Kategorien: ' + ', '.join(c[0] for c in selected),
		'Elemente: {0}, Typen: {1}, eindeutige Kombinationen: {2}'.format(n_all, len(type_cache), len(combos)),
		'Siemens-typisch: {0} ({1})'.format(sum(s['siemens'] for s in cat_stats.values()),
			percent(sum(s['siemens'] for s in cat_stats.values()), n_all)),
		ZWP_LP8 + ' angehakt: {0}'.format(sum(s['lp8'] for s in cat_stats.values())),
		'Kostengruppen-Parameter gefunden: ' + (', '.join(sorted(n for n in params if KG_PARAM_PATTERN.search(n))) or 'keiner'),
		'Datenbank: ' + ('{0} Modellnamen fehlen'.format(missing) if database is not None else 'nicht angegeben'),
		lv_summary,
		'Verknuepfungen: {0} (geladen: {1})'.format(n_links, n_links_loaded),
		'Ansichtsfilter: {0}'.format(len(filters)),
		'Worksharing: ' + ('ja' if workshared else 'nein'),
		'Ergebnisordner: ' + folder,
	]
	with io.open(os.path.join(folder, '0_Zusammenfassung.txt'), 'w', encoding='utf-8-sig') as f:
		f.write(u'\r\n'.join(summary) + u'\r\n')
	return '\n'.join(summary)


OUT = run()
