# -*- coding: utf-8 -*-
"""Anzeige des Zustands am Button "Nachtrag starten".

Beschriftung, Tooltip und Symbol des Buttons zeigen, ob und welcher
Nachtrag im aktiven Projekt aktiv ist (z. B. "Nachtrag 2 aktiv").
Wechselt der Benutzer zu einem anderen Projekt, passt der Idling-Handler
(hinweise.py) die Anzeige an.
"""

import os
import re

import clr
clr.AddReference("PresentationCore")
from System import Uri
from System.Windows.Media.Imaging import BitmapCacheOption, BitmapImage

from ga_nachtrag import config
from ga_nachtrag.eingabe import button_beschriftung, button_tooltip

_ERWEITERUNG = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
_START_BUTTON_ORDNER = os.path.join(
    _ERWEITERUNG,
    config.REITER_NAME + ".tab",
    config.GRUPPE_NAME + ".panel",
    "Nachtrag starten.pushbutton")
SYMBOL_INAKTIV = os.path.join(_START_BUTTON_ORDNER, "icon.png")
SYMBOL_AKTIV = os.path.join(_START_BUTTON_ORDNER, "icon_aktiv.png")


def aktualisiere_button(uiapp, nachtrag):
    """Passt den Start-Button an den Zustand an.

    Gibt False zurück, wenn der Button (noch) nicht gefunden wurde.
    """
    button = finde_start_button(uiapp)
    if button is None:
        return False
    beschriftung = button_beschriftung(nachtrag)
    tooltip = button_tooltip(nachtrag)
    if button.ItemText == beschriftung and button.ToolTip == tooltip:
        return True  # Anzeige ist aktuell
    button.ItemText = beschriftung
    button.ToolTip = tooltip
    symbol = SYMBOL_AKTIV if nachtrag is not None else SYMBOL_INAKTIV
    if hasattr(button, "LargeImage") and os.path.exists(symbol):
        button.LargeImage = lade_symbol(symbol, 32)
    return True


def finde_start_button(uiapp):
    """Sucht den pyRevit-Button "Nachtrag starten" im Reiter "Nachtrag"."""
    try:
        gruppen = uiapp.GetRibbonPanels(config.REITER_NAME)
    except Exception:
        return None  # Reiter existiert (noch) nicht
    for gruppe in gruppen:
        for eintrag in gruppe.GetItems():
            if "nachtragstarten" in _normalisiere(eintrag.Name):
                return eintrag
    return None


def lade_symbol(pfad, groesse):
    bild = BitmapImage()
    bild.BeginInit()
    bild.UriSource = Uri(pfad)
    bild.CacheOption = BitmapCacheOption.OnLoad
    bild.DecodePixelHeight = groesse
    bild.EndInit()
    return bild


def _normalisiere(name):
    # pyRevit vergibt interne Namen wie "ga_nachtrag-nachtrag-...-nachtragstarten"
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())
