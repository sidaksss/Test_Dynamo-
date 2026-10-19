# -*- coding: utf-8 -*-
"""Prototyp (Entwurf): KI-gestuetzte Uebersetzungstabelle Kombination -> LV-Position.

Laeuft AUSSERHALB von Revit, nur mit der Python-Standardbibliothek (CPython3),
damit derselbe Code spaeter auch in einem Dynamo-Python-Knoten laufen kann.

Ablauf je eindeutiger Kombination (nicht je Bauteil):
  1. Regel:       Modell bzw. Typname = Leistungsnummer/L-Identifizierer/Materialnummer
                  -> Quelle "Regel", keine KI
  2. Kandidaten:  lokale Aehnlichkeitssuche liefert hoechstens 5 LV-Kandidaten
  3. KI:          waehlt NUR aus K1..K5 oder KEINE (festes Antwortschema), mit Begruendung
  4. Vertrauen:   aus Uebereinstimmung KI <-> lokaler Bestwert + Punktzahl, nicht aus der
                  Selbsteinschaetzung der KI allein
  5. Ausgabe:     Uebersetzungstabelle (CSV). Spalte "Freigabe" fuellt ein Mensch.
                  Dynamo liest spaeter nur Zeilen mit Freigabe = ja.

Schluessel: NUR aus der Umgebungsvariablen KI_API_KEY (oder ANTHROPIC_API_KEY).
Ohne Schluessel: TESTMODUS mit festen Beispielantworten (deutlich gekennzeichnet).

Aufruf:
  python ki_zuordnung_prototyp.py <kombinationen.csv> <sap_lv.xlsx> <ausgabeordner> [--referenz <referenz.csv>]

Umgebungsvariablen (alle optional ausser dem Schluessel fuer echte Anfragen):
  KI_API_KEY / ANTHROPIC_API_KEY  Schluessel
  KI_API_URL      Standard https://api.anthropic.com/v1/messages
  KI_MODELL       Standard claude-opus-5-5
  KI_EFFORT       Standard low (Klassifikation braucht wenig Nachdenken)
  KI_CA_DATEI     Pfad zu einem Firmen-Stammzertifikat (bei TLS-Pruefung im Firmennetz)
  HTTPS_PROXY     Firmen-Proxy, wird automatisch verwendet

Status: Entwurf, nur mit Beispieldaten im Testmodus getestet. Echter API-Test steht aus.
Stil: keine f-Strings, Tabs, io.open mit Kodierung."""

import csv
import difflib
import hashlib
import io
import json
import os
import re
import ssl
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

try:
	import urllib.request as urlrequest
	import urllib.error as urlerror
except ImportError:  # pragma: no cover
	urlrequest = None

PROMPT_VERSION = 'v1-2026-10'
MAX_CANDIDATES = 5
LABELS = ['K1', 'K2', 'K3', 'K4', 'K5']
MIN_SCORE = 0.15
STOPWORDS = set(['fuer', 'für', 'mit', 'und', 'oder', 'der', 'die', 'das', 'den', 'dem', 'ein', 'eine',
	'von', 'zur', 'zum', 'bis', 'auf', 'aus', 'bei', 'als', 'inkl', 'typ', 'type', 'st', 'stk', 'mm', 'ja', 'nein'])

API_URL = os.environ.get('KI_API_URL', 'https://api.anthropic.com/v1/messages')
API_KEY = os.environ.get('KI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY') or ''
MODEL = os.environ.get('KI_MODELL', 'claude-opus-5-5')
EFFORT = os.environ.get('KI_EFFORT', 'low')
CA_FILE = os.environ.get('KI_CA_DATEI', '')
TEST_MODE = not API_KEY

# Festes Antwortschema: die KI kann nur K1..K5 oder KEINE waehlen.
ANSWER_SCHEMA = {
	'type': 'object',
	'properties': {
		'wahl': {'type': 'string', 'enum': LABELS + ['KEINE']},
		'sicherheit': {'type': 'string', 'enum': ['hoch', 'mittel', 'niedrig']},
		'begruendung': {'type': 'string'},
	},
	'required': ['wahl', 'sicherheit', 'begruendung'],
	'additionalProperties': False,
}

SYSTEM_PROMPT = (u'Du ordnest Bauteile der Gebaeudeautomation aus einem Revit-Modell Positionen eines '
	u'Leistungsverzeichnisses (LV) zu. Du bekommst die Angaben eines Bauteiltyps und bis zu fuenf '
	u'Kandidaten K1 bis K5 aus dem LV. Waehle den Kandidaten, der dasselbe Produkt bzw. dieselbe Leistung '
	u'beschreibt. Wenn keiner sicher passt, waehle KEINE. Erfinde keine Positionen. Begruende kurz '
	u'(hoechstens zwei Saetze) mit den Merkmalen, die uebereinstimmen oder fehlen.')


# --- Text -------------------------------------------------------------------

def nospace(text):
	return re.sub(r'\s+', '', text or '').upper()


def model_keys(text):
	words = re.sub(r'\s+', ' ', text or '').strip().upper().split(' ')
	result = []
	for c in (''.join(words), words[0], ''.join(words[:2])):
		if c and c not in result:
			result.append(c)
	return result


def tokens(text):
	result = set()
	for w in re.split(r'[^0-9A-Za-zÄÖÜäöüß.\-/]+', (text or '').lower()):
		w = w.strip('.-/')
		if len(w) < 2 or w in STOPWORDS or re.match(r'^[\d.,\-/]+$', w):
			continue
		result.add(w)
	return result


def is_code(token):
	return bool(re.search(r'[a-zäöü]', token)) and bool(re.search(r'\d', token))


# --- Eingaben ---------------------------------------------------------------

def read_csv(path):
	for encoding in ('utf-8-sig', 'cp1252'):
		try:
			with io.open(path, 'r', encoding=encoding, newline='') as f:
				return list(csv.DictReader(f, delimiter=';'))
		except UnicodeDecodeError:
			continue
	return []


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
			col = 0
			for ch in re.match(r'[A-Z]+', c.get('r')).group(0):
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
	"""Abrechenbare LV-Zeilen (ohne Titel, Hinweise, Masterzeilen). Preise werden NICHT gelesen."""
	rows = read_xlsx_rows(path)
	header = [h.strip().lower() for h in rows[0]]

	def col(*names):
		for n in names:
			if n.lower() in header:
				return header.index(n.lower())
		return None

	c = dict(pos=col('ext. Leistungsnummer', 'LV-Positionsnummer'), nr=col('Leistungsnummer'),
		lid=col('L-Identifizierer'), mat=col('Materialnummer'), typ=col('Objekttyp'),
		t1=col('Kurztextzeile 1', 'Kurztext'), t2=col('Kurztextzeile 2'), lang=col('Langtext'))
	positions = []
	for row in rows[1:]:
		get = lambda k: row[c[k]].strip() if c[k] is not None and c[k] < len(row) else ''
		if not get('pos') or not get('nr') or get('typ') == 'M':
			continue
		text = ' '.join(x for x in (get('t1'), get('t2'), get('lang')) if x)
		codes = []
		for k in ('nr', 'lid', 'mat'):
			if get(k) and nospace(get(k)) not in codes:
				codes.append(nospace(get(k)))
		positions.append({'pos': get('pos'), 'nr': get('nr'), 'codes': codes, 'text': text,
			'tokens': tokens(text + ' ' + get('nr') + ' ' + get('lid'))})
	return positions


# --- Regel und Aehnlichkeit --------------------------------------------------

def rule_match(sap, combo):
	keys = model_keys(combo['Modell']) + model_keys(combo['Typ'])
	hits = [p for p in sap if any(k in p['codes'] for k in keys)]
	return hits


def similarity(element_tokens, product_text, position):
	if not position['tokens']:
		return 0.0
	hit = 0.0
	weight = 0.0
	for t in position['tokens']:
		w = 3.0 if is_code(t) else 1.0
		weight += w
		if t in element_tokens:
			hit += w
		elif len(t) >= 5 and any(t in e or (len(e) >= 5 and e in t) for e in element_tokens):
			hit += w * 0.5
	text_score = difflib.SequenceMatcher(None, product_text.lower(), position['text'].lower()).ratio() if product_text else 0.0
	return round(0.7 * hit / weight + 0.3 * text_score, 2)


def candidates(sap, combo):
	text = ' '.join(combo[k] for k in ('Familie', 'Typ', 'Modell', 'Kommentar', 'RDS_Funktion') if combo.get(k))
	product = ' '.join(combo[k] for k in ('Typ', 'Modell', 'Kommentar') if combo.get(k))
	scored = [(similarity(tokens(text), product, p), p) for p in sap]
	scored = [sp for sp in scored if sp[0] >= MIN_SCORE]
	scored.sort(key=lambda sp: (-sp[0], sp[1]['pos']))
	return scored[:MAX_CANDIDATES]


# --- KI-Aufruf ----------------------------------------------------------------

def build_user_text(combo, cands):
	lines = [u'Bauteiltyp:',
		u'  Familie: ' + combo.get('Familie', ''),
		u'  Typ: ' + combo.get('Typ', ''),
		u'  Modell: ' + (combo.get('Modell', '') or '(leer)'),
		u'  Kommentar: ' + (combo.get('Kommentar', '') or '(leer)'),
		u'  RDS-Funktion: ' + (combo.get('RDS_Funktion', '') or '(leer)'),
		u'', u'Kandidaten aus dem LV:']
	for label, (score, p) in zip(LABELS, cands):
		lines.append(u'  {0}: Leistungsnummer {1} | {2}'.format(label, p['nr'], p['text']))
	return u'\n'.join(lines)


def cache_key(user_text):
	raw = json.dumps([MODEL, PROMPT_VERSION, SYSTEM_PROMPT, ANSWER_SCHEMA, user_text], sort_keys=True, ensure_ascii=False)
	return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def load_cache(path):
	cache = {}
	if os.path.isfile(path):
		with io.open(path, 'r', encoding='utf-8') as f:
			for line in f:
				if line.strip():
					entry = json.loads(line)
					cache[entry['key']] = entry['antwort']
	return cache


def append_cache(path, key, answer):
	with io.open(path, 'a', encoding='utf-8') as f:
		f.write(json.dumps({'key': key, 'antwort': answer}, ensure_ascii=False) + u'\n')


# Feste Beispielantworten fuer den TESTMODUS (Schluessel = Typname der Beispiel-Kombination)
TEST_ANSWERS = {
	'Modul 8 Kanal LCD': {'wahl': 'K1', 'sicherheit': 'hoch', 'begruendung': 'TESTMODUS: 8 Kanaele, Hand und LCD wie K1.'},
	'Sensor': {'wahl': 'KEINE', 'sicherheit': 'niedrig', 'begruendung': 'TESTMODUS: zu wenige Angaben.'},
}


def call_ai(user_text, combo):
	"""Gibt (antwort_dict, fehlertext) zurueck."""
	if TEST_MODE:
		answer = TEST_ANSWERS.get(combo.get('Typ', ''),
			{'wahl': 'K1', 'sicherheit': 'mittel', 'begruendung': 'TESTMODUS: feste Beispielantwort (bester lokaler Kandidat).'})
		return dict(answer), ''
	body = {
		'model': MODEL,
		'max_tokens': 2000,
		'system': SYSTEM_PROMPT,
		'messages': [{'role': 'user', 'content': user_text}],
		'output_config': {'effort': EFFORT, 'format': {'type': 'json_schema', 'schema': ANSWER_SCHEMA}},
	}
	headers = {'content-type': 'application/json', 'x-api-key': API_KEY, 'anthropic-version': '2023-06-01'}
	if 'api.anthropic.com' in API_URL:
		# Server-seitige Ausweichloesung bei Ablehnung (nur auf der Anthropic-API verfuegbar)
		body['fallbacks'] = 'default'
		headers['anthropic-beta'] = 'server-side-fallback-2026-07-01'
	data = json.dumps(body).encode('utf-8')
	context = ssl.create_default_context(cafile=CA_FILE) if CA_FILE else ssl.create_default_context()
	opener = urlrequest.build_opener(urlrequest.ProxyHandler(), urlrequest.HTTPSHandler(context=context))
	last_error = ''
	for attempt in range(4):
		try:
			request = urlrequest.Request(API_URL, data=data, headers=headers, method='POST')
			with opener.open(request, timeout=60) as response:
				result = json.loads(response.read().decode('utf-8'))
			stop = result.get('stop_reason')
			if stop == 'refusal':
				return None, 'KI hat die Anfrage abgelehnt'
			if stop == 'max_tokens':
				return None, 'Antwort abgeschnitten (max_tokens)'
			text = ''.join(b.get('text', '') for b in result.get('content', []) if b.get('type') == 'text')
			answer = json.loads(text)
			if answer.get('wahl') not in LABELS + ['KEINE']:
				return None, 'ungueltige Wahl: ' + str(answer.get('wahl'))
			return answer, ''
		except urlerror.HTTPError as ex:
			last_error = 'HTTP ' + str(ex.code)
			if ex.code in (408, 409, 429) or ex.code >= 500:
				time.sleep(2 ** attempt)
				continue
			return None, last_error + ' (nicht wiederholbar)'
		except (urlerror.URLError, ValueError, OSError) as ex:
			last_error = str(ex)
			time.sleep(2 ** attempt)
	return None, 'KI nicht erreichbar: ' + last_error


# --- Vertrauen -------------------------------------------------------------------

def confidence(answer, cands):
	"""HOCH / MITTEL / NIEDRIG aus Uebereinstimmung mit dem lokalen Bestwert, Punktzahl und KI-Sicherheit."""
	if answer is None or answer['wahl'] == 'KEINE' or not cands:
		return 'NIEDRIG'
	index = LABELS.index(answer['wahl'])
	agrees = index == 0
	score = cands[index][0]
	if agrees and score >= 0.5 and answer['sicherheit'] == 'hoch':
		return 'HOCH'
	if agrees or answer['sicherheit'] == 'hoch':
		return 'MITTEL'
	return 'NIEDRIG'


# --- Hauptablauf -----------------------------------------------------------------

def combo_key(row):
	return row.get('Modell') or row.get('Typ') or (row.get('Familie', '') + '|' + row.get('Typ', ''))


def build_table(combos, sap, cache_path, use_ai=True):
	"""Gibt Zeilen der Uebersetzungstabelle zurueck. use_ai=False = Variante ohne KI."""
	cache = load_cache(cache_path) if use_ai else {}
	table = []
	seen = set()
	for row in combos:
		combo = dict((k, (row.get(k) or '').strip()) for k in ('Kategorie', 'Familie', 'Typ', 'Modell', 'Kommentar', 'RDS_Funktion'))
		key = combo_key(combo)
		if key in seen:
			continue
		seen.add(key)
		out = {'Schluessel': key, 'Freigabe': '', 'LV-Position': '', 'Quelle': '', 'Vertrauen': '',
			'Begruendung': '', 'Kandidaten': '', 'Hinweis': ''}
		hits = rule_match(sap, combo)
		positions = sorted(set(h['pos'] for h in hits))
		if len(positions) == 1:
			out.update({'LV-Position': positions[0], 'Quelle': 'Regel', 'Vertrauen': 'HOCH',
				'Begruendung': 'Modell bzw. Typname = Leistungsnummer'})
			table.append(out)
			continue
		if len(positions) > 1:
			out.update({'Quelle': 'Regel', 'Vertrauen': 'MEHRDEUTIG', 'Kandidaten': ', '.join(positions),
				'Begruendung': 'Produkt steht in mehreren LV-Positionen; Abschnitt waehlt ein Mensch'})
			table.append(out)
			continue
		cands = candidates(sap, combo)
		out['Kandidaten'] = ' | '.join('{0}={1} ({2})'.format(l, p['pos'], s) for l, (s, p) in zip(LABELS, cands))
		if not cands:
			out.update({'Quelle': 'keine Kandidaten', 'Vertrauen': 'NIEDRIG'})
			table.append(out)
			continue
		if not use_ai:
			score, best = cands[0]
			out.update({'LV-Position': best['pos'], 'Quelle': 'Aehnlichkeit',
				'Vertrauen': 'MITTEL' if score >= 0.5 else 'NIEDRIG', 'Begruendung': 'bester lokaler Kandidat'})
			table.append(out)
			continue
		user_text = build_user_text(combo, cands)
		key_hash = cache_key(user_text)
		if key_hash in cache:
			answer, error = cache[key_hash], ''
			out['Hinweis'] = 'aus Zwischenspeicher'
		else:
			answer, error = call_ai(user_text, combo)
			if answer is not None and not TEST_MODE:
				append_cache(cache_path, key_hash, answer)
		if answer is None:
			score, best = cands[0]
			out.update({'LV-Position': best['pos'], 'Quelle': 'Aehnlichkeit (KI-Fehler)', 'Vertrauen': 'NIEDRIG',
				'Hinweis': error})
		else:
			chosen = '' if answer['wahl'] == 'KEINE' else cands[LABELS.index(answer['wahl'])][1]['pos']
			out.update({'LV-Position': chosen, 'Quelle': 'KI-TESTMODUS' if TEST_MODE else 'KI ' + MODEL,
				'Vertrauen': confidence(answer, cands), 'Begruendung': answer['begruendung']})
		table.append(out)
	return table


def evaluate(table, reference):
	"""Kennzahlen gegen eine Referenz (Schluessel;LV-Position). MEHRDEUTIG und NIEDRIG gelten als 'zu pruefen'."""
	ref = dict(((r.get('Schluessel') or '').strip(), (r.get('LV-Position') or '').strip()) for r in reference)
	n = auto = correct_auto = wrong_auto = review = correct_any = 0
	for row in table:
		if row['Schluessel'] not in ref:
			continue
		n += 1
		truth = ref[row['Schluessel']]
		if row['LV-Position'] == truth:
			correct_any += 1
		if row['Vertrauen'] in ('HOCH', 'MITTEL') and row['LV-Position']:
			auto += 1
			if row['LV-Position'] == truth:
				correct_auto += 1
			else:
				wrong_auto += 1
		else:
			review += 1
	pct = lambda a, b: '{0:.0f} %'.format(100.0 * a / b) if b else '-'
	return {'Kombinationen mit Referenz': n, 'Trefferquote (bester Vorschlag richtig)': pct(correct_any, n),
		'automatisch vorgeschlagen (HOCH/MITTEL)': pct(auto, n), 'davon falsch': pct(wrong_auto, auto),
		'zu pruefen (NIEDRIG/MEHRDEUTIG)': pct(review, n)}


def write_table(path, table):
	fields = ['Schluessel', 'Freigabe', 'LV-Position', 'Quelle', 'Vertrauen', 'Begruendung', 'Kandidaten', 'Hinweis']
	with io.open(path, 'w', encoding='utf-8-sig', newline='') as f:
		writer = csv.DictWriter(f, fieldnames=fields, delimiter=';')
		writer.writeheader()
		for row in table:
			writer.writerow(row)


def main(argv):
	if len(argv) < 4:
		print(__doc__)
		return 1
	combos = read_csv(argv[1])
	sap = read_sap(argv[2])
	folder = argv[3]
	if not os.path.isdir(folder):
		os.makedirs(folder)
	cache_path = os.path.join(folder, 'ki_zwischenspeicher.jsonl')
	mode = 'TESTMODUS (kein Schluessel, feste Beispielantworten)' if TEST_MODE else 'ECHT: ' + MODEL + ' ueber ' + API_URL
	print('Modus: ' + mode)
	table_ai = build_table(combos, sap, cache_path, use_ai=True)
	name = 'uebersetzungstabelle_TESTMODUS.csv' if TEST_MODE else 'uebersetzungstabelle.csv'
	write_table(os.path.join(folder, name), table_ai)
	print('Tabelle: ' + os.path.join(folder, name) + ' (' + str(len(table_ai)) + ' Kombinationen)')
	if '--referenz' in argv:
		reference = read_csv(argv[argv.index('--referenz') + 1])
		table_plain = build_table(combos, sap, cache_path, use_ai=False)
		if TEST_MODE:
			print('ACHTUNG: Im TESTMODUS sind die KI-Antworten fest vorgegeben. Die Kennzahlen "mit KI"')
			print('pruefen nur den Ablauf und sagen NICHTS ueber die Qualitaet einer echten KI aus.')
		for label, table in (('ohne KI (Regel + Aehnlichkeit)', table_plain), ('mit KI' + (' [TESTMODUS]' if TEST_MODE else ''), table_ai)):
			print('Kennzahlen ' + label + ':')
			for k, v in evaluate(table, reference).items():
				print('  ' + k + ': ' + str(v))
	return 0


if __name__ == '__main__':
	sys.exit(main(sys.argv))
