# -*- coding: utf-8 -*-
"""Dynamic Model Updater (IUpdater) des Nachtragsmodus.

Revit ruft Execute auf, wenn GA-Bauteile hinzugefügt oder gelöscht
werden, und zwar innerhalb der laufenden Transaktion. Hinzugefügte
Bauteile werden gekennzeichnet, beim Löschen erscheint nur ein Hinweis.
"""

from System import AppDomain, Guid
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    BuiltInCategory,
    ChangePriority,
    Element,
    ElementIsElementTypeFilter,
    ElementMulticategoryFilter,
    IUpdater,
    LogicalAndFilter,
    UpdaterId,
    UpdaterRegistry,
)

from ga_nachtrag import config, hinweise, zustand
from ga_nachtrag.kennzeichnung import kennzeichne_bauteile
from ga_nachtrag.parameter import ga_kategorien

SCHLUESSEL_UPDATER_ID = "GA_Nachtrag.UpdaterId"

HINWEIS_LOESCHEN = (u"Bauteile nicht löschen, sondern als entfallen markieren. "
                    u"Rückgängig mit Strg+Z.")


class NachtragsUpdater(IUpdater):
    """Kennzeichnet neue GA-Bauteile mit dem aktiven Nachtrag."""

    def __init__(self, addin_id):
        self._updater_id = UpdaterId(addin_id, Guid(config.UPDATER_GUID))
        # Projekte, für die "Parameter fehlen" schon gemeldet wurde
        self._gemeldete_projekte = set()

    def GetUpdaterId(self):
        return self._updater_id

    def GetUpdaterName(self):
        return "GA Nachtragsmodus"

    def GetAdditionalInformation(self):
        return ("Kennzeichnet neu platzierte GA-Bauteile mit Nachtragsnummer "
                "und Grund (pyRevit-Erweiterung GA_Nachtrag). Optional: "
                "ohne pyRevit wird das Modell normal bearbeitet.")

    def GetChangePriority(self):
        return ChangePriority.MEPFixtures

    def Execute(self, daten):
        # Ausnahmen dürfen Revit nie erreichen, sonst deaktiviert Revit den
        # Updater und zeigt dem Benutzer eine Fehlermeldung.
        try:
            doc = daten.GetDocument()
            if doc.IsFamilyDocument:
                return
            neue_ids = daten.GetAddedElementIds()
            if neue_ids.Count > 0:
                self.verarbeite_neue_bauteile(doc, neue_ids)
            if daten.GetDeletedElementIds().Count > 0:
                hinweise.merke_hinweis(HINWEIS_LOESCHEN)
        except Exception as fehler:
            hinweise.merke_hinweis(
                u"Interner Fehler im Nachtragsmodus, es wurde nichts "
                u"gekennzeichnet: {}".format(fehler))

    def verarbeite_neue_bauteile(self, doc, neue_ids):
        nachtrag = zustand.lies_aktiven_nachtrag(doc)
        ergebnis = kennzeichne_bauteile(doc, neue_ids, nachtrag)
        self.melde_ergebnis(doc, nachtrag, ergebnis)

    def melde_ergebnis(self, doc, nachtrag, ergebnis):
        """Merkt Hinweise zu Problemen vor. Erfolgsfälle bleiben still."""
        if ergebnis.ohne_parameter and nachtrag is not None:
            # Nur einmal je Projekt und Sitzung melden
            if doc.Title not in self._gemeldete_projekte:
                self._gemeldete_projekte.add(doc.Title)
                hinweise.merke_hinweis(
                    u"Nachtrag {} aktiv, aber NT_Nachtragsnummer/NT_Grund "
                    u"fehlen im Projekt '{}' für: {}. Diese Bauteile wurden "
                    u"nicht gekennzeichnet.".format(
                        nachtrag.nummer, doc.Title,
                        u", ".join(sorted(ergebnis.ohne_parameter))))
        if ergebnis.nicht_im_besitz:
            hinweise.merke_hinweis(
                u"{} neue Bauteile wurden nicht verändert, weil sie nicht "
                u"Ihnen gehören (Worksharing).".format(ergebnis.nicht_im_besitz))
        if ergebnis.fehler:
            hinweise.merke_hinweis(
                u"{} Bauteile konnten nicht gekennzeichnet werden:\n{}".format(
                    len(ergebnis.fehler), u"\n".join(ergebnis.fehler[:10])))


def erstelle_ga_filter():
    """Filter: nur Exemplare (keine Typen) der konfigurierten GA-Kategorien."""
    kategorien = List[BuiltInCategory](ga_kategorien())
    nur_exemplare = ElementIsElementTypeFilter(True)
    return LogicalAndFilter(ElementMulticategoryFilter(kategorien), nur_exemplare)


def registriere_updater(uiapp):
    """Registriert den Updater global (für alle Dokumente) als optional.

    Optional heißt: Wer das Modell ohne pyRevit öffnet, erhält keine
    Warnung über einen fehlenden Updater.
    """
    melde_alten_updater_ab()
    updater = NachtragsUpdater(uiapp.ActiveAddInId)
    updater_id = updater.GetUpdaterId()
    UpdaterRegistry.RegisterUpdater(updater, True)
    ga_filter = erstelle_ga_filter()
    UpdaterRegistry.AddTrigger(updater_id, ga_filter,
                               Element.GetChangeTypeElementAddition())
    UpdaterRegistry.AddTrigger(updater_id, ga_filter,
                               Element.GetChangeTypeElementDeletion())
    AppDomain.CurrentDomain.SetData(SCHLUESSEL_UPDATER_ID, updater_id)
    return updater


def melde_alten_updater_ab():
    """Entfernt einen Updater aus einem früheren Laden (pyRevit "Reload")."""
    alte_id = AppDomain.CurrentDomain.GetData(SCHLUESSEL_UPDATER_ID)
    if alte_id is not None and UpdaterRegistry.IsUpdaterRegistered(alte_id):
        UpdaterRegistry.UnregisterUpdater(alte_id)


def ist_updater_aktiv():
    """True, wenn der Updater registriert und nicht deaktiviert ist."""
    updater_id = AppDomain.CurrentDomain.GetData(SCHLUESSEL_UPDATER_ID)
    if updater_id is None:
        return False
    return (UpdaterRegistry.IsUpdaterRegistered(updater_id)
            and UpdaterRegistry.IsUpdaterEnabled(updater_id))
