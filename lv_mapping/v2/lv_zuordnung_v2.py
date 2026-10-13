# -*- coding: utf-8 -*-
"""Dynamo Python Script node: LV-Zuordnung v2 (Erweiterung von
lv_mapping/lv_nummer_zuweisen.py).

Ablauf je Bauteil der gewaehlten Kategorien:
  0. LV-Nummer schon vorhanden            -> behalten (nie ueberschreiben)
  1. Datenbank-CSV: Modell / Typname        -> LV-Nummer      (sicher)
  2. SAP-LV: Modell = Leistungsnummer, L-Identifizierer oder Materialnummer
  3. SAP-LV: Leistungsnummer steckt im Typ- oder Familiennamen
     -> genau eine LV-Position: sicher; mehrere: Vorschlagsliste "mehrdeutig"
  4. Aehnlichkeitssuche ueber ALLE Text-Parameter des Bauteils gegen
     Leistungsnummer, Hersteller-Typ und Kurztext im SAP-LV
     -> nur Vorschlag mit Punktzahl, wird NIE automatisch geschrieben

Geschrieben wird nur, wenn IN[3] = True, und nur bei sicheren Treffern
(Stufen 1-3, eindeutig). Alles andere landet in der Vorschlagsliste
(eine Zeile je Kombination). Bestaetigte Zeilen werden in die
Datenbank-CSV uebernommen und gelten ab dem naechsten Lauf (Pflege nur einmal).

Inputs:  IN[0] SAP-LV-Export (.xlsx), optional
         IN[1] Datenbank-CSV (Schluessel;LV-Nummer), optional
         IN[2] Name des Zielparameters (leer = 'LV_Nummer')
         IN[3] In Modell schreiben (True/False, Standard False = Testlauf)
Output:  Zusammenfassung als Text; Dateien in LV_Zuordnung_<Zeit> auf dem Desktop.

Planerparameter (Praefix ZWP_) werden nicht gelesen.
Status: Prototyp, nur gegen Beispieldaten getestet. Test in echtem Revit steht aus.
Kompatibel mit CPython3 und PythonNet3 (keine f-Strings)."""

import datetime
import difflib
import io
import os
import re
import zipfile
import xml.etree.ElementTree as ET

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


def text_input(value):
	return '' if value is None else str(value).strip()


SAP_PATH = text_input(IN[0])
DB_PATH = text_input(IN[1])
TARGET = text_input(IN[2]) or 'LV_Nummer'
WRITE = IN[3] is True

PLANNER_PREFIX = 'ZWP_'
# ANNAHME: Grenzen fuer die Punktzahl der Aehnlichkeitssuche (0..1)
STRONG = 0.75
MEDIUM = 0.5
MIN_SCORE = 0.2  # darunter kein Vorschlag
MAX_SUGGESTIONS = 3
# Woerter ohne Aussagekraft fuer den Vergleich
STOPWORDS = set(['fuer', 'für', 'mit', 'und', 'oder', 'der', 'die', 'das', 'den', 'dem', 'ein', 'eine',
	'von', 'zur', 'zum', 'bis', 'auf', 'aus', 'bei', 'als', 'inkl', 'typ', 'type', 'st', 'stk', 'mm', 'nein', 'ja'])


# --- Texte normalisieren ---------------------------------------------------

def collapse(text):
	return re.sub(r'\s+', ' ', text or '').strip().upper()


def nospace(text):
	return re.sub(r'\s+', '', text or '').upper()


def model_keys(text):
	"""Vergleichsschluessel: ganz ohne Leerzeichen, erstes Wort, erste zwei Woerter."""
	words = collapse(text).split(' ')
	result = []
	for c in (''.join(words), words[0], ''.join(words[:2])):
		if c and c not in result:
			result.append(c)
	return result


def tokens(text):
	words = re.split(r'[^0-9A-Za-zÄÖÜäöüß.\-/]+', (text or '').lower())
	result = set()
	for w in words:
		w = w.strip('.-/')
		if len(w) < 2 or w in STOPWORDS or re.match(r'^[\d.,\-/]+$', w):
			continue
		result.add(w)
	return result


def is_code(token):
	"""Produktcode: Buchstaben und Ziffern gemischt, z. B. qam2112.040."""
	return bool(re.search(r'[a-zäöü]', token)) and bool(re.search(r'\d', token))


# --- Datenbank-CSV und SAP-LV ------------------------------------------------

def read_lines(path):
	for encoding in ('utf-8-sig', 'cp1252'):
		try:
			with io.open(path, 'r', encoding=encoding) as f:
				return f.read().splitlines()
		except UnicodeDecodeError:
			continue
	return []


def read_database(path):
	"""Schluessel (Modell oder Typname) -> LV-Nummer. Weitere Spalten werden ignoriert."""
	mapping = {}
	conflicts = set()
	for line in read_lines(path):
		cleaned = line.replace('"', '').strip().strip(';,\t ')
		parts = re.split(r'[;\t]', cleaned)
		if len(parts) < 2:
			parts = cleaned.split(',')
		if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
			continue
		key = nospace(parts[0])
		if key in ('MODELL', 'MODEL', 'TYPNAME', 'TYP', 'SCHLUESSEL', 'SCHLÜSSEL'):
			continue
		lv = parts[1].strip()
		if key in mapping and mapping[key] != lv:
			conflicts.add(key)
		mapping.setdefault(key, lv)
	return mapping, conflicts


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


def read_sap(path):
	"""Abrechenbare Zeilen des SAP-LV (ohne Titel-, Hinweis- und Masterzeilen)."""
	rows = read_xlsx_rows(path)
	header = [h.strip().lower() for h in rows[0]]

	def col(*names):
		for n in names:
			if n.lower() in header:
				return header.index(n.lower())
		return None

	c = dict(pos=col('ext. Leistungsnummer', 'LV-Positionsnummer', 'Positionsnummer'), nr=col('Leistungsnummer'),
		lid=col('L-Identifizierer'), mat=col('Materialnummer'), typ=col('Objekttyp'),
		t1=col('Kurztextzeile 1', 'Kurztext'), t2=col('Kurztextzeile 2'), einheit=col('Basismengeneinheit'))
	positions = []
	for row in rows[1:]:
		get = lambda k: row[c[k]].strip() if c[k] is not None and c[k] < len(row) else ''
		if not get('pos') or not get('nr') or get('typ') == 'M':
			continue
		text = (get('t1') + ' ' + get('t2')).strip()
		codes = []
		for k in ('nr', 'lid', 'mat'):
			if get(k) and nospace(get(k)) not in codes:
				codes.append(nospace(get(k)))
		positions.append({'pos': get('pos'), 'nr': get('nr'), 'codes': codes, 'text': text,
			'einheit': get('einheit'), 'tokens': tokens(text + ' ' + ' '.join([get('nr'), get('lid'), get('mat')]))})
	return positions


# --- Stufen 2-4 ----------------------------------------------------------------

def exact_matches(sap, modell, typ, familie):
	"""Stufe 2 (Modell) und 3 (Typ-/Familienname). Gibt (Stufe, Positionen) zurueck."""
	keys = model_keys(modell)
	hits = [p for p in sap if any(k in p['codes'] for k in keys)]
	if hits:
		return 'Modell = Leistungsnummer', hits
	names = nospace(typ) + '|' + nospace(familie)
	hits = [p for p in sap if any(len(code) >= 5 and code in names for code in p['codes'])]
	if hits:
		return 'Leistungsnummer im Typ-/Familiennamen', hits
	return '', []


def similarity(element_tokens, product_text, position):
	"""Punktzahl 0..1 aus Produktcode-, Wort- und Textaehnlichkeit."""
	lv_tokens = position['tokens']
	if not lv_tokens:
		return 0.0
	hit = 0.0
	weight = 0.0
	for t in lv_tokens:
		w = 3.0 if is_code(t) else 1.0
		weight += w
		if t in element_tokens:
			hit += w
		elif len(t) >= 5 and any(t in e or (len(e) >= 5 and e in t) for e in element_tokens):
			hit += w * 0.5
	word_score = hit / weight
	text_score = difflib.SequenceMatcher(None, product_text.lower(), position['text'].lower()).ratio() if product_text else 0.0
	return round(0.7 * word_score + 0.3 * text_score, 2)


def suggest(sap, element_tokens, product_text):
	scored = []
	for p in sap:
		score = similarity(element_tokens, product_text, p)
		if score >= MIN_SCORE:
			scored.append((score, p))
	scored.sort(key=lambda sp: (-sp[0], sp[1]['pos']))
	return scored[:MAX_SUGGESTIONS]


def rating(score):
	if score >= STRONG:
		return 'stark'
	if score >= MEDIUM:
		return 'mittel'
	return 'schwach'


# --- Revit ------------------------------------------------------------------

def id_value(element_id):
	value = getattr(element_id, 'Value', None)  # Revit 2024+
	if value is None:
		value = element_id.IntegerValue
	return int(value)


def param_text(p):
	if p is None:
		return ''
	if p.StorageType == StorageType.String:
		return (p.AsString() or '').strip()
	return ''


def bip_text(element, built_in):
	return param_text(element.get_Parameter(built_in)) if element is not None else ''


def all_texts(element):
	"""Alle Text-Parameter eines Elements (ohne Planerparameter)."""
	texts = []
	if element is None:
		return texts
	for p in element.Parameters:
		name = p.Definition.Name
		if name.startswith(PLANNER_PREFIX) or name.startswith('RDS_') or name == TARGET:
			continue
		value = param_text(p)
		if value and len(value) < 200:
			texts.append(value)
	return texts


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
	form.Text = 'LV-Zuordnung v2 - ' + ('SCHREIBEN' if WRITE else 'Testlauf (nichts wird geschrieben)')
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
	form.Controls.Add(box)
	form.Controls.Add(buttons)
	form.Controls.Add(label)
	form.AcceptButton = ok
	form.CancelButton = cancel
	if form.ShowDialog() != DialogResult.OK:
		return None
	return [categories[int(i)] for i in box.CheckedIndices]


# --- Ausgabe -------------------------------------------------------------------

def csv_field(value):
	text = '' if value is None else str(value)
	if ';' in text or '"' in text or '\n' in text:
		text = '"' + text.replace('"', '""') + '"'
	return text


def write_csv(path, rows):
	lines = [';'.join(csv_field(v) for v in row) for row in rows]
	with io.open(path, 'w', encoding='utf-8-sig', newline='') as f:
		f.write(u'\r\n'.join(lines) + u'\r\n')


COPILOT_INTRO = u"""Du hilfst bei der Zuordnung von Revit-Bauteilen (Gebaeudeautomation) zu Positionen eines Leistungsverzeichnisses (LV).
Fuer jedes Bauteil unten stehen seine Angaben und bis zu {0} Kandidaten aus dem LV.
Waehle je Bauteil die passende LV-Position oder schreibe "keine", wenn keine passt. Rate nicht.
Antworte NUR als CSV mit Semikolon und dieser Kopfzeile:
Schluessel;LV-Nummer;Begruendung

""".format(MAX_SUGGESTIONS)


# --- Hauptablauf -----------------------------------------------------------------

def run():
	if not SAP_PATH and not DB_PATH:
		return 'FEHLER: Bitte SAP-LV (.xlsx) und/oder Datenbank-CSV angeben.'
	sap = read_sap(SAP_PATH) if SAP_PATH and os.path.isfile(SAP_PATH) else []
	database, conflicts = read_database(DB_PATH) if DB_PATH and os.path.isfile(DB_PATH) else ({}, set())
	if not sap and not database:
		return 'FEHLER: Weder SAP-LV noch Datenbank konnten gelesen werden.'

	selected = ask_for_categories(model_categories_with_elements(doc))
	if not selected:
		return 'Abgebrochen bzw. keine Kategorie angehakt. Es wurde nichts veraendert.'

	type_cache = {}
	combos = {}
	results = []      # je Bauteil
	writes = []       # (Ziel-Element, Wert, Bauteil-ID)

	for cat_name, cat_id, _ in selected:
		for el in FilteredElementCollector(doc).OfCategoryId(cat_id).WhereElementIsNotElementType():
			tid = el.GetTypeId()
			tkey = id_value(tid) if tid is not None else -1
			if tkey not in type_cache:
				t = doc.GetElement(tid) if tkey >= 0 else None
				type_cache[tkey] = {
					'el': t,
					'familie': bip_text(t, BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM),
					'typ': bip_text(t, BuiltInParameter.SYMBOL_NAME_PARAM),
					'modell': bip_text(t, BuiltInParameter.ALL_MODEL_MODEL),
					'texts': all_texts(t),
				}
			ti = type_cache[tkey]
			familie, typ = ti['familie'], ti['typ']
			modell = bip_text(el, BuiltInParameter.ALL_MODEL_MODEL) or ti['modell']
			kommentar = bip_text(el, BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
			eid = id_value(el.Id)

			# Ziel: Exemplarparameter, sonst Typparameter
			target_el, p = el, el.LookupParameter(TARGET)
			if p is None and ti['el'] is not None:
				target_el, p = ti['el'], ti['el'].LookupParameter(TARGET)
			row = [eid, cat_name, familie, typ, modell, kommentar]
			if p is None or p.StorageType != StorageType.String:
				results.append(row + ['', 'Fehler', "Zielparameter '" + TARGET + "' fehlt oder ist kein Text", ''])
				continue
			if (p.AsString() or '').strip():
				results.append(row + [p.AsString(), 'vorhanden', 'nicht ueberschrieben', ''])
				continue

			# Stufe 1: Datenbank (Modell, dann Typname)
			lv = None
			for k in model_keys(modell) + [nospace(typ)]:
				if k and k in database:
					if k in conflicts:
						lv = 'KONFLIKT'
					else:
						lv = database[k]
					break
			if lv and lv != 'KONFLIKT':
				results.append(row + [lv, 'sicher', 'Datenbank', ''])
				writes.append((target_el, lv, eid, p))
				continue

			# Stufen 2-3: SAP-LV exakt
			stage, hits = exact_matches(sap, modell, typ, familie) if sap else ('', [])
			positions = sorted(set(h['pos'] for h in hits))
			if len(positions) == 1:
				results.append(row + [positions[0], 'sicher', stage, ''])
				writes.append((target_el, positions[0], eid, p))
				continue

			# Vorschlagsliste je Kombination
			ckey = (cat_name, familie, typ, modell, kommentar)
			if ckey not in combos:
				texts = [modell, typ, familie, kommentar] + ti['texts'] + all_texts(el)
				product_text = ' '.join(x for x in (modell, typ, bip_text(ti['el'], BuiltInParameter.ALL_MODEL_DESCRIPTION)) if x)
				if lv == 'KONFLIKT':
					reason, cands = 'Datenbank enthaelt widerspruechliche LV-Nummern', []
				elif len(positions) > 1:
					reason = 'mehrdeutig: Produkt steht in mehreren LV-Positionen'
					cands = [(1.0, h) for h in hits][:MAX_SUGGESTIONS * 3]
				elif sap:
					reason = 'kein exakter Treffer: Aehnlichkeitssuche'
					cands = suggest(sap, tokens(' '.join(texts)), product_text)
				else:
					reason, cands = 'kein Treffer in der Datenbank', []
				combos[ckey] = {'n': 0, 'reason': reason, 'cands': cands, 'texts': texts}
			combos[ckey]['n'] += 1
			best = combos[ckey]['cands'][0] if combos[ckey]['cands'] else None
			results.append(row + ['', 'Vorschlag' if best else 'offen', combos[ckey]['reason'],
				(best[1]['pos'] + ' (' + str(best[0]) + ')') if best else ''])

	# Schreiben: nur sichere Treffer, Typparameter nur bei einheitlichem Wert
	written = 0
	write_errors = []
	if WRITE and writes:
		by_target = {}
		for target_el, value, eid, p in writes:
			key = id_value(target_el.Id)
			by_target.setdefault(key, {'p': p, 'values': set(), 'ids': []})
			by_target[key]['values'].add(value)
			by_target[key]['ids'].append(eid)
		TransactionManager.Instance.EnsureInTransaction(doc)
		try:
			for key, info in by_target.items():
				if len(info['values']) > 1:
					write_errors.append([key, 'Typparameter, aber unterschiedliche LV-Nummern: ' + ', '.join(sorted(info['values']))])
					continue
				try:
					if info['p'].IsReadOnly:
						raise Exception('schreibgeschuetzt')
					info['p'].Set(list(info['values'])[0])
					written += len(info['ids'])
				except Exception as ex:
					write_errors.append([key, 'Schreiben fehlgeschlagen (belegt oder gesperrt?): ' + str(ex)])
		finally:
			TransactionManager.Instance.TransactionTaskDone()

	# Dateien
	folder = os.path.join(System.Environment.GetFolderPath(System.Environment.SpecialFolder.Desktop),
		'LV_Zuordnung_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
	os.makedirs(folder)
	write_csv(os.path.join(folder, '1_Ergebnis_je_Bauteil.csv'),
		[['Element-ID', 'Kategorie', 'Familie', 'Typ', 'Modell', 'Kommentar', 'LV-Nummer', 'Status', 'Quelle / Grund',
		'bester Vorschlag (Punktzahl)']] + results)

	header = ['Schluessel', 'LV-Nummer (hier bestaetigen)', 'Anzahl Bauteile', 'Grund']
	for i in range(1, MAX_SUGGESTIONS + 1):
		header += ['Vorschlag ' + str(i), 'Punktzahl ' + str(i), 'Bewertung ' + str(i), 'LV-Kurztext ' + str(i)]
	header += ['Kategorie', 'Familie', 'Typ', 'Modell', 'Kommentar']
	rows = [header]
	prompt = [COPILOT_INTRO]
	for ckey in sorted(combos, key=lambda k: -combos[k]['n']):
		c = combos[ckey]
		key = ckey[3] or ckey[2]  # Schluessel fuer die Datenbank: Modell, sonst Typname
		line = [key, '', c['n'], c['reason']]
		for i in range(MAX_SUGGESTIONS):
			if i < len(c['cands']):
				score, pos = c['cands'][i]
				line += [pos['pos'], score, rating(score) if 'mehrdeutig' not in c['reason'] else 'mehrdeutig', pos['text']]
			else:
				line += ['', '', '', '']
		rows.append(line + list(ckey))
		prompt.append(u'Schluessel: {0}\nBauteil: Kategorie={1}; Familie={2}; Typ={3}; Modell={4}; Kommentar={5}'.format(
			key, ckey[0], ckey[1], ckey[2], ckey[3], ckey[4]))
		prompt.append(u'Weitere Angaben: ' + '; '.join(sorted(set(t for t in c['texts'] if t)))[:400])
		for score, pos in c['cands']:
			prompt.append(u'  Kandidat {0} | Leistungsnummer {1} | {2} | Einheit {3}'.format(pos['pos'], pos['nr'], pos['text'], pos['einheit']))
		prompt.append(u'')
	write_csv(os.path.join(folder, '2_Vorschlaege.csv'), rows)
	with io.open(os.path.join(folder, '3_Copilot_Anfrage.txt'), 'w', encoding='utf-8-sig') as f:
		f.write(u'\r\n'.join(prompt))
	if write_errors:
		write_csv(os.path.join(folder, '4_Schreibfehler.csv'), [['Ziel-Element-ID', 'Problem']] + write_errors)

	status = {}
	for r in results:
		status[r[7]] = status.get(r[7], 0) + 1
	return '\n'.join(line for line in [
		'FERTIG - ' + ('es wurde GESCHRIEBEN' if WRITE else 'TESTLAUF: es wurde nichts geschrieben'),
		'Kategorien: ' + ', '.join(c[0] for c in selected),
		'SAP-LV: {0} Positionen; Datenbank: {1} Eintraege'.format(len(sap), len(database)),
		'Bauteile: {0}'.format(len(results)),
		'  sicher zugeordnet: {0}'.format(status.get('sicher', 0)),
		'  schon vorhanden (nicht ueberschrieben): {0}'.format(status.get('vorhanden', 0)),
		'  Vorschlag zur Pruefung: {0}'.format(status.get('Vorschlag', 0)),
		'  offen ohne Vorschlag: {0}'.format(status.get('offen', 0)),
		'  Fehler (Zielparameter fehlt): {0}'.format(status.get('Fehler', 0)),
		'Kombinationen in der Vorschlagsliste: {0}'.format(len(combos)),
		('Geschrieben: {0} Bauteile; Schreibfehler: {1}'.format(written, len(write_errors)) if WRITE else ''),
		'Ergebnisordner: ' + folder,
	] if line)


OUT = run()
