# -*- coding: utf-8 -*-
"""Prüfung der Benutzereingaben und Darstellung des aktiven Nachtrags.

Dieses Modul nutzt bewusst keine Revit-API, damit es auch außerhalb von
Revit getestet werden kann (siehe pyrevit/tests).
"""

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


def kodiere_nachtrag(nachtrag):
    """Wandelt den Nachtrag in einen Text "nummer|grund" um.

    So kann er zwischen den pyRevit-Skripten und dem Updater
    ausgetauscht werden. Kein Nachtrag -> leerer Text.
    """
    if nachtrag is None:
        return u""
    return u"{}|{}".format(nachtrag.nummer, nachtrag.grund)


def dekodiere_nachtrag(text):
    """Gegenstück zu kodiere_nachtrag. Ungültiger Text -> None."""
    if not text or u"|" not in text:
        return None
    nummer_text, grund = text.split(u"|", 1)
    nummer, fehler_nummer = pruefe_nachtragsnummer(nummer_text)
    grund, fehler_grund = pruefe_grund(grund)
    if fehler_nummer or fehler_grund:
        return None
    return Nachtrag(nummer, grund)


def button_beschriftung(nachtrag):
    """Beschriftung des Start-Buttons, abhängig vom Zustand."""
    if nachtrag is None:
        return u"Nachtrag\nstarten"
    return u"Nachtrag {}\naktiv".format(nachtrag.nummer)


def button_tooltip(nachtrag):
    """Tooltip des Start-Buttons, abhängig vom Zustand."""
    if nachtrag is None:
        return (u"Kein Nachtrag aktiv. Neu platzierte GA-Bauteile gelten als "
                u"möglicher Vertragsstand.\nKlicken, um einen Nachtrag zu "
                u"starten.")
    return (u"Aktiv: Nachtrag {}\nGrund: {}\nNeu platzierte GA-Bauteile "
            u"werden diesem Nachtrag zugeordnet.\nKlicken, um den Nachtrag "
            u"zu wechseln.".format(nachtrag.nummer, nachtrag.grund))
