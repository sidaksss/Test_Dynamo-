# -*- coding: utf-8 -*-
"""Zugriff auf die NT-Parameter und Prüfung des geöffneten Projekts.

Die Parameter werden über ihre GUID aus der Shared-Parameter-Datei gesucht.
Ein gleichnamiger Parameter mit anderer GUID gilt als fehlend.
"""

from System import Guid
from Autodesk.Revit.DB import (
    BuiltInCategory,
    Category,
    FilteredElementCollector,
    InstanceBinding,
    ParameterElement,
    SharedParameterElement,
    StorageType,
)

from ga_nachtrag import config


class Projektpruefung(object):
    """Ergebnis von pruefe_projektparameter.

    fehler:   Probleme, bei denen nichts geschrieben werden darf.
    hinweise: Probleme, bei denen der Modus trotzdem nutzbar ist
              (z. B. Parameter nicht allen GA-Kategorien zugeordnet).
    """

    def __init__(self):
        self.fehler = []
        self.hinweise = []

    @property
    def ist_ok(self):
        return not self.fehler


def ga_kategorien():
    """Liste der konfigurierten GA-Kategorien als BuiltInCategory."""
    kategorien = []
    for name in config.GA_KATEGORIEN:
        kategorie = getattr(BuiltInCategory, name, None)
        if kategorie is not None:
            kategorien.append(kategorie)
    return kategorien


def unbekannte_kategorien():
    """Kategorienamen aus config.py, die es in dieser Revit-Version nicht gibt."""
    return [name for name in config.GA_KATEGORIEN
            if getattr(BuiltInCategory, name, None) is None]


def hole_nachtragsparameter(element):
    """Gibt (NT_Nachtragsnummer, NT_Grund) des Bauteils zurück.

    Fehlt ein Parameter am Bauteil, ist der jeweilige Wert None.
    """
    nummer = element.get_Parameter(Guid(config.GUID_NACHTRAGSNUMMER))
    grund = element.get_Parameter(Guid(config.GUID_GRUND))
    return nummer, grund


def hat_passenden_speichertyp(parameter_nummer, parameter_grund):
    """Prüft, ob Nummer eine Ganzzahl und Grund ein Text ist."""
    return (parameter_nummer.StorageType == StorageType.Integer
            and parameter_grund.StorageType == StorageType.String)


def pruefe_projektparameter(doc):
    """Prüft, ob NT_Nachtragsnummer und NT_Grund im Projekt richtig angelegt
    sind: vorhanden (richtige GUID), Exemplarparameter, GA-Kategorien
    zugeordnet."""
    pruefung = Projektpruefung()
    for name, guid_text in config.PARAMETER_STUFE_1:
        _pruefe_einen_parameter(doc, name, guid_text, pruefung)
    falsche_namen = unbekannte_kategorien()
    if falsche_namen:
        pruefung.hinweise.append(
            u"Unbekannte Kategorien in config.py werden ignoriert: {}"
            .format(u", ".join(falsche_namen)))
    return pruefung


def _pruefe_einen_parameter(doc, name, guid_text, pruefung):
    parameter = SharedParameterElement.Lookup(doc, Guid(guid_text))
    if parameter is None:
        if _gibt_es_parameter_mit_namen(doc, name):
            pruefung.fehler.append(
                u"'{}' ist vorhanden, stammt aber nicht aus "
                u"GA_Nachtrag_SharedParameters_v2.txt (andere GUID)."
                .format(name))
        else:
            pruefung.fehler.append(
                u"'{}' fehlt im Projekt.".format(name))
        return

    definition = parameter.GetDefinition()
    bindungen = doc.ParameterBindings
    if not bindungen.Contains(definition):
        pruefung.fehler.append(
            u"'{}' ist als Shared Parameter geladen, aber keiner Kategorie "
            u"als Projektparameter zugeordnet.".format(name))
        return

    bindung = bindungen.get_Item(definition)
    if not isinstance(bindung, InstanceBinding):
        pruefung.fehler.append(
            u"'{}' ist als Typparameter angelegt, muss aber ein "
            u"Exemplarparameter sein.".format(name))
        return

    fehlende = _nicht_zugeordnete_ga_kategorien(doc, bindung)
    if fehlende:
        pruefung.hinweise.append(
            u"'{}' ist folgenden GA-Kategorien nicht zugeordnet: {}. "
            u"Bauteile dieser Kategorien werden nicht gekennzeichnet."
            .format(name, u", ".join(fehlende)))


def _nicht_zugeordnete_ga_kategorien(doc, bindung):
    fehlende = []
    for kategorie_enum in ga_kategorien():
        kategorie = Category.GetCategory(doc, kategorie_enum)
        if kategorie is None:
            continue  # Kategorie im Projekt nicht vorhanden
        if not bindung.Categories.Contains(kategorie):
            fehlende.append(kategorie.Name)
    return fehlende


def _gibt_es_parameter_mit_namen(doc, name):
    for parameter in FilteredElementCollector(doc).OfClass(ParameterElement):
        if parameter.Name == name:
            return True
    return False
