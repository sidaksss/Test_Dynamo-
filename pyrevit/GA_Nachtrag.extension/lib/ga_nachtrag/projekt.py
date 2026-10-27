# -*- coding: utf-8 -*-
"""Bestimmt die Projektdatei, an die ein Nachtrag gebunden ist."""

from Autodesk.Revit.DB import ModelPathUtils

from ga_nachtrag.eingabe import normalisiere_projektschluessel


def projektschluessel(doc):
    """Eindeutiger Schlüssel der Projektdatei.

    Worksharing: Pfad des Zentralmodells. Alle lokalen Kopien desselben
    Zentralmodells haben damit denselben Schlüssel.
    Sonst: Pfad der Projektdatei (bzw. Cloud-Pfad).
    Nie gespeichertes Projekt oder Familie: None.
    """
    if doc is None or doc.IsFamilyDocument:
        return None
    if doc.IsWorkshared and not doc.IsDetached:
        zentralmodell = doc.GetWorksharingCentralModelPath()
        if zentralmodell is not None:
            return _schluessel_aus_modellpfad(zentralmodell)
    if doc.IsModelInCloud:
        return _schluessel_aus_modellpfad(doc.GetCloudModelPath())
    return normalisiere_projektschluessel(doc.PathName)


def aktives_projekt(uiapp):
    """Das aktive Projekt oder None (kein Dokument offen bzw. Familie)."""
    uidoc = uiapp.ActiveUIDocument
    if uidoc is None or uidoc.Document.IsFamilyDocument:
        return None
    return uidoc.Document


def _schluessel_aus_modellpfad(modellpfad):
    return normalisiere_projektschluessel(
        ModelPathUtils.ConvertModelPathToUserVisiblePath(modellpfad))
