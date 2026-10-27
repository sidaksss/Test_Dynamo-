# -*- coding: utf-8 -*-
"""Prüfung der Benutzereingaben, Speicherformat und Darstellung der
aktiven Nachträge.

Dieses Modul nutzt bewusst keine Revit-API, damit es auch außerhalb von
Revit getestet werden kann (siehe pyrevit/tests).
"""

import json
import re

from ga_nachtrag import config

# Größter Wert eines Revit-Ganzzahlparameters (Int32)
GROESSTE_NACHTRAGSNUMMER = 2147483647

_NUR_ZIFFERN = re.compile(r"^[0-9]+$")


class Nachtrag(object):
    """Aktiver Nachtrag: Nachtragsnummer (Ganzzahl > 0) und Grund."""

    def __init__(self, nummer, grund):
        self.nummer = nummer
        self.grund = grund

    def __eq__(self, anderer):
        return (isinstance(anderer, Nachtrag)
                and self.nummer == anderer.nummer
                and self.grund == anderer.grund)

    def __ne__(self, anderer):
        return not self.__eq__(anderer)

    def __repr__(self):
        return "Nachtrag({!r}, {!r})".format(self.nummer, self.grund)


def pruefe_nachtragsnummer(text):
    """Prüft die Eingabe der Nachtragsnummer.

    Erlaubt sind nur Ziffern (0-9) mit einem Wert größer 0,
    z. B. "2". Abgelehnt werden z. B. "N2", "0", "-1", "2.0".
    Rückgabe: (nummer, fehlermeldung) - genau eins von beiden ist None.
    """
    text = (text or u"").strip()
    if not text:
        return None, u"Bitte eine Nachtragsnummer eingeben."
    if not _NUR_ZIFFERN.match(text):
        return None, (u"Die Nachtragsnummer darf nur aus Ziffern bestehen "
                      u"(z. B. 2), ohne Buchstaben oder Zeichen.")
    nummer = int(text)
    if nummer <= 0:
        return None, u"Die Nachtragsnummer muss größer als 0 sein."
    if nummer > GROESSTE_NACHTRAGSNUMMER:
        return None, u"Die Nachtragsnummer ist zu groß."
    return nummer, None


def pruefe_grund(text):
    """Prüft den Grund des Nachtrags (Pflichtfeld, kurz, einzeilig).

    Rückgabe: (grund, fehlermeldung) - genau eins von beiden ist None.
    """
    grund = (text or u"").strip()
    if not grund:
        return None, u"Bitte einen Grund für den Nachtrag eingeben."
    if u"\n" in grund or u"\r" in grund:
        return None, u"Der Grund darf nur eine Zeile lang sein."
    if len(grund) > config.MAX_LAENGE_GRUND:
        return None, (u"Der Grund ist zu lang (höchstens {} Zeichen)."
                      .format(config.MAX_LAENGE_GRUND))
    return grund, None


def normalisiere_projektschluessel(pfad):
    """Vereinheitlicht einen Dateipfad zum Schlüssel einer Projektdatei.

    Windows-Pfade sind nicht von Groß-/Kleinschreibung abhängig, deshalb
    wird alles klein geschrieben und "\\" durch "/" ersetzt.
    Leerer Pfad (Projekt nie gespeichert) -> None.
    """
    pfad = (pfad or u"").strip()
    if not pfad:
        return None
    return pfad.replace(u"\\", u"/").lower()


def kodiere_nachtraege(nachtraege):
    """Wandelt {Projektschlüssel: Nachtrag} in einen JSON-Text um.

    So werden die aktiven Nachträge gespeichert und zwischen den
    pyRevit-Skripten und dem Updater ausgetauscht.
    """
    daten = {}
    for schluessel, nachtrag in nachtraege.items():
        daten[schluessel] = {"nummer": nachtrag.nummer, "grund": nachtrag.grund}
    return json.dumps(daten, sort_keys=True)


def dekodiere_nachtraege(text):
    """Gegenstück zu kodiere_nachtraege. Ungültige Einträge entfallen."""
    if isinstance(text, dict):
        daten = text
    else:
        try:
            daten = json.loads(text) if text else {}
        except ValueError:
            return {}
    if not isinstance(daten, dict):
        return {}
    nachtraege = {}
    for schluessel, eintrag in daten.items():
        if not isinstance(eintrag, dict):
            continue
        nummer, fehler_nummer = pruefe_nachtragsnummer(
            u"{}".format(eintrag.get("nummer", u"")))
        grund, fehler_grund = pruefe_grund(eintrag.get("grund"))
        if fehler_nummer is None and fehler_grund is None:
            nachtraege[schluessel] = Nachtrag(nummer, grund)
    return nachtraege


def button_beschriftung(nachtrag):
    """Beschriftung des Start-Buttons, abhängig vom Zustand."""
    if nachtrag is None:
        return u"Nachtrag\nstarten"
    return u"Nachtrag {}\naktiv".format(nachtrag.nummer)


def button_tooltip(nachtrag):
    """Tooltip des Start-Buttons, abhängig vom Zustand."""
    if nachtrag is None:
        return (u"In diesem Projekt ist kein Nachtrag aktiv. Neu platzierte "
                u"GA-Bauteile gelten als möglicher Vertragsstand.\nKlicken, "
                u"um einen Nachtrag zu starten.")
    return (u"In diesem Projekt aktiv: Nachtrag {}\nGrund: {}\nNeu "
            u"platzierte GA-Bauteile werden diesem Nachtrag zugeordnet."
            u"\nKlicken, um den Nachtrag zu wechseln."
            .format(nachtrag.nummer, nachtrag.grund))
