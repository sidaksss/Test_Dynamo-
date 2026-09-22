# -*- coding: utf-8 -*-
"""Dynamo Python Script node 0: sucht fuer jedes Bauteil der aktiven Ansicht
den Wert des Shared Parameters 'Typ' (z. B. 'QMX2.P33') in einer Excel-Tabelle
mit den Spalten 'LV Nummer' und 'Typ' und schreibt die gefundene LV Nummer in
den Shared Parameter 'LV Nummer' zurueck.

Ablauf:
  1. Lesephase (kein Transaction): Elemente der aktiven Ansicht durchgehen,
     Excel-Treffer suchen, Konflikte (Feld bereits anders befuellt) sofort per
     TaskDialog abfragen. Es wird bewusst NICHT waehrend einer offenen
     Transaction ein UI-Dialog gezeigt.
  2. Schreibphase (eine Transaction): alle bestaetigten Werte setzen.
  3. Sammel-Meldung fuer Elemente ohne Treffer in der Excel-Liste.

Compatible with IronPython2 and CPython3 (no f-strings, no walrus)."""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from Autodesk.Revit.DB import FilteredElementCollector
from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons, TaskDialogResult

doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
active_view = uiapp.ActiveUIDocument.ActiveView

excel_rows = IN[0]
typ_param_name = IN[1] if len(IN) > 1 and IN[1] else 'Typ'
lv_param_name = IN[2] if len(IN) > 2 and IN[2] else 'LV Nummer'
ask_before_overwrite = IN[3] if len(IN) > 3 else True


def is_header(row):
	if len(row) < 2:
		return False
	a = row[0].strip().lower() if isinstance(row[0], str) else ''
	b = row[1].strip().lower() if isinstance(row[1], str) else ''
	return a in ('lv nummer', 'lvnummer', 'lv_nummer') or b == 'typ'


# Excel-Zeilen -> Lookup-Dict {Typ: LV Nummer}. Spalte 0 = LV Nummer, Spalte 1 = Typ.
lookup = {}
for row in excel_rows:
	if not row or len(row) < 2 or is_header(row):
		continue
	lv_value, typ_value = row[0], row[1]
	if typ_value is None:
		continue
	key = str(typ_value).strip()
	if key:
		lookup[key] = lv_value

collector = FilteredElementCollector(doc, active_view.Id).WhereElementIsNotElementType()

to_write = []      # [(element, new_lv_str, log_entry)]
not_found = []      # log strings
declined = []      # log strings

for el in collector:
	typ_param = el.LookupParameter(typ_param_name)
	lv_param = el.LookupParameter(lv_param_name)
	if typ_param is None or lv_param is None:
		continue

	typ_value = typ_param.AsString()
	if not typ_value or not typ_value.strip():
		continue
	typ_value = typ_value.strip()

	if typ_value not in lookup:
		not_found.append('ID {0}: Typ "{1}"'.format(el.Id.IntegerValue, typ_value))
		continue

	new_lv = lookup[typ_value]
	new_lv_str = '' if new_lv is None else str(new_lv).strip()
	current_lv = lv_param.AsString()
	current_lv = current_lv.strip() if current_lv else ''

	if current_lv == new_lv_str:
		continue

	if current_lv and ask_before_overwrite:
		td = TaskDialog('LV Nummer ueberschreiben?')
		td.MainInstruction = 'Element-ID {0}  |  Typ: {1}'.format(el.Id.IntegerValue, typ_value)
		td.MainContent = (
			'Vorhandene LV Nummer: {0}\n'
			'Neue LV Nummer aus Excel: {1}\n\n'
			'Vorhandenen Wert ueberschreiben?'
		).format(current_lv, new_lv_str)
		td.CommonButtons = TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No
		result = td.Show()
		if result != TaskDialogResult.Yes:
			declined.append('ID {0}: Typ "{1}" (behalten: {2})'.format(el.Id.IntegerValue, typ_value, current_lv))
			continue

	to_write.append((el, new_lv_str, 'ID {0}: {1} -> {2}'.format(el.Id.IntegerValue, typ_value, new_lv_str)))

updated = []

TransactionManager.Instance.EnsureInTransaction(doc)
for el, new_lv_str, log_entry in to_write:
	el.LookupParameter(lv_param_name).Set(new_lv_str)
	updated.append(log_entry)
TransactionManager.Instance.TransactionTaskDone()

if not_found:
	preview = not_found[:25]
	msg = 'Fuer folgende Elemente wurde kein passender Eintrag in der Excel-Liste gefunden:\n\n'
	msg += '\n'.join(preview)
	if len(not_found) > 25:
		msg += '\n... und {0} weitere (siehe OUT[1])'.format(len(not_found) - 25)
	td_nf = TaskDialog('Keine Uebereinstimmung gefunden')
	td_nf.MainContent = msg
	td_nf.Show()

OUT = [updated, not_found, declined]
