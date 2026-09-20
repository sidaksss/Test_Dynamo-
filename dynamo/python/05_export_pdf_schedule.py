# -*- coding: utf-8 -*-
"""Dynamo Python Script node 5: builds (or reuses) a filtered Revit
schedule that only shows elements tagged with the current Nachtrag_Nummer,
then exports that schedule to PDF via the native Revit export so the PDF
always matches the shared-parameter state written by node 3."""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from Autodesk.Revit.DB import (
	ViewSchedule, FilteredElementCollector, BuiltInCategory,
	ScheduleFilter, ScheduleFilterType, ElementId, PDFExportOptions
)

doc = DocumentManager.Instance.CurrentDBDocument

nachtrag_nummer = IN[0]
category_bic_names = IN[1]
export_folder = IN[2]
file_name = IN[3]

category_map = {
	'MSR_Geraete': BuiltInCategory.OST_MechanicalEquipment,
	'Schaltschraenke': BuiltInCategory.OST_ElectricalEquipment,
	'Kabeltrassen': BuiltInCategory.OST_CableTray,
}

TransactionManager.Instance.EnsureInTransaction(doc)

schedule_name = 'Nachtrag_' + nachtrag_nummer
existing = [v for v in FilteredElementCollector(doc).OfClass(ViewSchedule)
			if v.Name == schedule_name]

if existing:
	schedule = existing[0]
else:
	bic = category_map.get(category_bic_names[0], BuiltInCategory.OST_MechanicalEquipment)
	schedule = ViewSchedule.CreateSchedule(doc, ElementId(bic))
	schedule.Name = schedule_name

	fields = schedule.Definition.GetSchedulableFields()
	target_names = [
		'LV_Positionsnummer', 'LV_Kurztext', 'Basismengeneinheit',
		'Nachtrag_Status', 'Nachtrag_Erstversion', 'Nachtrag_Nummer',
		'Nachtrag_Freigabestatus', 'Nachtrag_Bemerkung',
	]
	for field in fields:
		if field.GetName(doc) in target_names:
			schedule.Definition.AddField(field)

	nachtrag_field = next(f for f in fields if f.GetName(doc) == 'Nachtrag_Nummer')
	schedule.Definition.AddFilter(ScheduleFilter(
		nachtrag_field, ScheduleFilterType.Equal, nachtrag_nummer))

TransactionManager.Instance.TransactionTaskDone()

options = PDFExportOptions()
options.FileName = file_name

doc.Export(export_folder, [schedule.Id], options)

OUT = schedule
