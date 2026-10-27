# -*- coding: utf-8 -*-
"""Aktive Nachträge: pro Benutzer lokal, je Projektdatei, nie im Modell.

Zu jeder Projektdatei (Schlüssel siehe projekt.py) kann ein Nachtrag aktiv
sein. Ein in Projekt A gestarteter Nachtrag wirkt nicht in Projekt B.

Die Zuordnung liegt an zwei Stellen:
1. Dauerhaft in der pyRevit-Benutzerkonfiguration (pyRevit_config.ini im
   Benutzerprofil). So bleibt sie nach einem Neustart von Revit erhalten.
2. Zur Laufzeit im .NET-AppDomain-Speicher von Revit. Jeder pyRevit-Button
   läuft in einer eigenen Python-Umgebung; der Updater liest die Zuordnung
   deshalb nicht aus der Python-Konfiguration, sondern aus diesem
   gemeinsamen Speicher.
"""

from System import AppDomain

from ga_nachtrag import config
from ga_nachtrag.eingabe import Nachtrag, dekodiere_nachtraege, kodiere_nachtraege
from ga_nachtrag.projekt import projektschluessel

SCHLUESSEL_AKTIVE_NACHTRAEGE = "GA_Nachtrag.AktiveNachtraege"
OPTION_AKTIVE_NACHTRAEGE = "aktive_nachtraege"


def lies_aktiven_nachtrag(doc):
    """Gibt den aktiven Nachtrag des Projekts zurück oder None (Modus aus)."""
    schluessel = projektschluessel(doc)
    if schluessel is None:
        return None
    return lies_alle_nachtraege().get(schluessel)


def starte_nachtrag(doc, nummer, grund):
    """Setzt den aktiven Nachtrag für dieses Projekt und diesen Benutzer."""
    nachtrag = Nachtrag(nummer, grund)
    nachtraege = lies_alle_nachtraege()
    nachtraege[projektschluessel(doc)] = nachtrag
    _speichere(nachtraege)
    return nachtrag


def beende_nachtrag(doc):
    """Schaltet den Nachtragsmodus für dieses Projekt aus."""
    nachtraege = lies_alle_nachtraege()
    nachtraege.pop(projektschluessel(doc), None)
    _speichere(nachtraege)


def lies_alle_nachtraege():
    """{Projektschlüssel: Nachtrag} aller Projekte mit aktivem Nachtrag."""
    text = AppDomain.CurrentDomain.GetData(SCHLUESSEL_AKTIVE_NACHTRAEGE)
    if text is None:
        # Noch nicht geladen (z. B. Button vor dem Startskript ausgeführt)
        return lade_nachtraege_aus_benutzerkonfiguration()
    return dekodiere_nachtraege(text)


def lade_nachtraege_aus_benutzerkonfiguration():
    """Liest die gespeicherten Nachträge und übernimmt sie in die Laufzeit."""
    text = _konfig_abschnitt().get_option(OPTION_AKTIVE_NACHTRAEGE, u"")
    nachtraege = dekodiere_nachtraege(text)
    _setze_laufzeitwert(nachtraege)
    return nachtraege


def _speichere(nachtraege):
    from pyrevit import script
    _konfig_abschnitt().set_option(OPTION_AKTIVE_NACHTRAEGE,
                                   kodiere_nachtraege(nachtraege))
    script.save_config()
    _setze_laufzeitwert(nachtraege)


def _setze_laufzeitwert(nachtraege):
    AppDomain.CurrentDomain.SetData(SCHLUESSEL_AKTIVE_NACHTRAEGE,
                                    kodiere_nachtraege(nachtraege))


def _konfig_abschnitt():
    from pyrevit import script
    return script.get_config(config.KONFIG_ABSCHNITT)
