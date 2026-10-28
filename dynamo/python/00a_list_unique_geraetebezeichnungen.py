# -*- coding: utf-8 -*-
"""Dynamo Python Script node (eigenstaendig, keine weiteren Nodes noetig):
durchsucht das gesamte aktuelle Revit-Projekt nach Elementen, die den
Parameter 'GERAETEBEZEICHNUNG' oder 'Modell' besitzen (Instanz- oder
Typparameter), liest bevorzugt 'GERAETEBEZEICHNUNG', sonst 'Modell', und
liefert eine duplikatfreie, alphabetisch sortierte Liste der gefundenen
Werte. Elemente mit einem der beiden Parameter, aber ohne Wert, werden
separat als 'skipped' (Element-ID) ausgegeben; Elemente ohne beide
Parameter werden ignoriert (so bleibt die Liste auf GA-relevante
Bauteile beschraenkt, ohne dass Kategorien manuell ausgewaehlt werden
muessen).

Compatible with IronPython2 and CPython3 (no f-strings, no walrus)."""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.DB import FilteredElementCollector, ElementId

doc = DocumentManager.Instance.CurrentDBDocument

PRIMARY_PARAM = 'GERAETEBEZEICHNUNG'
FALLBACK_PARAM = 'Modell'


def get_type(element):
	type_id = element.GetTypeId()
	if type_id is None or type_id == ElementId.InvalidElementId:
		return None
	return doc.GetElement(type_id)


def find_param(element, name):
	p = element.LookupParameter(name)
	if p is not None:
		return p
	el_type = get_type(element)
	if el_type is not None:
		return el_type.LookupParameter(name)
	return None


def param_value(param):
	if param is None or not param.HasValue:
		return None
	val = param.AsString()
	if not val:
		val = param.AsValueString()
	return val.strip() if val else None


seen = set()
unique_values = []
skipped = []

collector = FilteredElementCollector(doc).WhereElementIsNotElementType()

for el in collector:
	if el is None:
		continue

	primary_param = find_param(el, PRIMARY_PARAM)
	fallback_param = find_param(el, FALLBACK_PARAM)
	if primary_param is None and fallback_param is None:
		continue

	value = param_value(primary_param)
	if not value:
		value = param_value(fallback_param)

	if not value:
		skipped.append(el.Id.IntegerValue)
		continue

	if value not in seen:
		seen.add(value)
		unique_values.append(value)

unique_values.sort()

OUT = [unique_values, skipped]
