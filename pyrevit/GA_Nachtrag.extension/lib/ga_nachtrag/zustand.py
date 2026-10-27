# -*- coding: utf-8 -*-
"""Aktiver Nachtrag: pro Benutzer lokal, nie im Modell.

Der Zustand liegt an zwei Stellen:
1. Dauerhaft in der pyRevit-Benutzerkonfiguration (pyRevit_config.ini im
   Benutzerprofil). So bleibt er nach einem Neustart von Revit erhalten.
2. Zur Laufzeit im .NET-AppDomain-Speicher von Revit. Jeder pyRevit-Button
   läuft in einer eigenen Python-Umgebung; der Updater liest den Zustand
   deshalb nicht aus der Python-Konfiguration, sondern aus diesem
   gemeinsamen Speicher.
"""

from System import AppDomain

from ga_nachtrag import config
from ga_nachtrag.eingabe import Nachtrag, kodiere_nachtrag, dekodiere_nachtrag

SCHLUESSEL_AKTIVER_NACHTRAG = "GA_Nachtrag.AktiverNachtrag"


def lies_aktiven_nachtrag():
    """Gibt den aktiven Nachtrag zurück oder None, wenn der Modus aus ist."""
    text = AppDomain.CurrentDomain.GetData(SCHLUESSEL_AKTIVER_NACHTRAG)
    if text is None:
        # Noch nicht geladen (z. B. Button vor dem Startskript ausgeführt)
        return lade_nachtrag_aus_benutzerkonfiguration()
    return dekodiere_nachtrag(text)


def starte_nachtrag(nummer, grund):
    """Setzt den aktiven Nachtrag für diesen Benutzer."""
    nachtrag = Nachtrag(nummer, grund)
    _speichere_in_benutzerkonfiguration(nachtrag)
    _setze_laufzeitwert(nachtrag)
    return nachtrag


def beende_nachtrag():
    """Schaltet den Nachtragsmodus für diesen Benutzer aus."""
    _speichere_in_benutzerkonfiguration(None)
    _setze_laufzeitwert(None)


def lade_nachtrag_aus_benutzerkonfiguration():
    """Liest den gespeicherten Nachtrag und übernimmt ihn in die Laufzeit."""
    abschnitt = _konfig_abschnitt()
    nummer = abschnitt.get_option("nummer", 0)
    grund = abschnitt.get_option("grund", u"")
    nachtrag = dekodiere_nachtrag(u"{}|{}".format(nummer, grund))
    _setze_laufzeitwert(nachtrag)
    return nachtrag


def _setze_laufzeitwert(nachtrag):
    AppDomain.CurrentDomain.SetData(SCHLUESSEL_AKTIVER_NACHTRAG,
                                    kodiere_nachtrag(nachtrag))


def _speichere_in_benutzerkonfiguration(nachtrag):
    from pyrevit import script
    abschnitt = _konfig_abschnitt()
    abschnitt.set_option("nummer", nachtrag.nummer if nachtrag else 0)
    abschnitt.set_option("grund", nachtrag.grund if nachtrag else u"")
    script.save_config()


def _konfig_abschnitt():
    from pyrevit import script
    return script.get_config(config.KONFIG_ABSCHNITT)
