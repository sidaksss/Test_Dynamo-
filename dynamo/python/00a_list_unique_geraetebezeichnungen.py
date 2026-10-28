# -*- coding: utf-8 -*-
"""Dynamo Python Script node: durchsucht eine vorgegebene Elementliste
(typischerweise ueber OOTB 'Categories' + 'All Elements of Category' fuer
die gewuenschten GA-Kategorien zusammengestellt, ohne View-Einschraenkung,
also das ganze Projekt) und liest je Element zuerst den Parameter
'GERAETEBEZEICHNUNG', bei leerem Wert ersatzweise 'Modell' (Fallback).
Beide Parameter werden sowohl auf der Instanz als auch - falls dort nicht
gefunden oder leer - auf dem zugehoerigen Elementtyp gesucht, da 'Modell'
bei vielen Familien ein Typparameter ist.

Ergebnis ist eine nach Duplikaten bereinigte, alphabetisch sortierte Liste
der gefundenen Bezeichnungen - Ausgangsbasis fuer eine eigene (Dummy-)
Datenbank. Elemente ohne Wert in beiden Parametern werden separat als
'skipped' ausgegeben, damit man die Vollstaendigkeit pruefen kann.

Compatible with IronPython2 and CPython3 (no f-strings, no walrus)."""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.DB import ElementId

doc = DocumentManager.Instance.CurrentDBDocument

elements = IN[0]
primary_param_name = IN[1] if len(IN) > 1 and IN[1] else 'GERAETEBEZEICHNUNG'
fallback_param_name = IN[2] if len(IN) > 2 and IN[2] else 'Modell'

if not isinstance(elements, list):
	elements = [elements]


def get_param_value(element, param_name):
	"""Sucht param_name zuerst auf dem Element selbst, dann auf dessen Typ."""
	p = element.LookupParameter(param_name)
	if p is not None and p.HasValue:
		val = p.AsString()
		if not val:
			val = p.AsValueString()
		if val and val.strip():
			return val.strip()

	type_id = element.GetTypeId()
	if type_id is not None and type_id != ElementId.InvalidElementId:
		el_type = doc.GetElement(type_id)
		if el_type is not None:
			tp = el_type.LookupParameter(param_name)
			if tp is not None and tp.HasValue:
				val = tp.AsString()
				if not val:
					val = tp.AsValueString()
				if val and val.strip():
					return val.strip()
	return None


seen = set()
unique_values = []
skipped = []

for el in elements:
	if el is None:
		continue

	value = get_param_value(el, primary_param_name)
	if not value:
		value = get_param_value(el, fallback_param_name)

	if not value:
		skipped.append(el.Id.IntegerValue)
		continue

	if value not in seen:
		seen.add(value)
		unique_values.append(value)

unique_values.sort()

OUT = [unique_values, skipped]
