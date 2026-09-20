# -*- coding: utf-8 -*-
"""Dynamo Python Script node 1: reads the Nachtrag-relevant shared
parameters off the current selection and builds one record per element.
Compatible with IronPython2 and CPython3 (no f-strings, no walrus)."""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from Autodesk.Revit.DB import Element

doc = DocumentManager.Instance.CurrentDBDocument

elements = IN[0]
quantity_param_name = IN[1]

if not isinstance(elements, list):
	elements = [elements]


def get_param_string(element, name):
	p = element.LookupParameter(name)
	if p is None:
		return None
	if p.StorageType.ToString() == 'String':
		return p.AsString()
	return p.AsValueString()


def get_quantity(element, param_name):
	if param_name:
		p = element.LookupParameter(param_name)
		if p is not None:
			val = p.AsDouble() if p.StorageType.ToString() == 'Double' else p.AsInteger()
			if val:
				return float(val)
	return 1.0


records = []
skipped = []

for el in elements:
	if el is None:
		continue
	unique_id = el.UniqueId
	lv_position = get_param_string(el, 'LV_Positionsnummer')
	if not lv_position:
		skipped.append(unique_id)
		continue
	records.append({
		'UniqueId': unique_id,
		'ElementId': el.Id.IntegerValue,
		'LV_Positionsnummer': lv_position,
		'LV_Kurztext': get_param_string(el, 'LV_Kurztext') or '',
		'Basismengeneinheit': get_param_string(el, 'Basismengeneinheit') or '',
		'Menge': get_quantity(el, quantity_param_name),
		'Kategorie': el.Category.Name if el.Category else '',
	})

OUT = [records, skipped]
