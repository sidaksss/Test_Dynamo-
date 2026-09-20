# -*- coding: utf-8 -*-
"""Dynamo Python Script node 3: writes the Nachtrag_* shared parameters
back onto the model elements, keyed by UniqueId. Runs inside a single
Revit transaction so the write is atomic."""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitServices')
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

element_updates = IN[0]
default_freigabestatus = IN[1]

TransactionManager.Instance.EnsureInTransaction(doc)

written = []
for update in element_updates:
	el = doc.GetElement(update['UniqueId'])
	if el is None:
		continue

	el.LookupParameter('Nachtrag_ElementGUID').Set(update['UniqueId'])
	el.LookupParameter('Nachtrag_Status').Set(update['Nachtrag_Status'])
	el.LookupParameter('Nachtrag_Erstversion').Set(update['Nachtrag_Erstversion'])
	el.LookupParameter('Nachtrag_Nummer').Set(update['Nachtrag_Nummer'])

	freigabe_param = el.LookupParameter('Nachtrag_Freigabestatus')
	if freigabe_param is not None and not freigabe_param.AsString():
		freigabe_param.Set(default_freigabestatus)

	written.append(update['UniqueId'])

TransactionManager.Instance.TransactionTaskDone()

OUT = written
