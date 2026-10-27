# -*- coding: utf-8 -*-
"""Nicht blockierende Hinweise für den Benutzer.

Der Updater darf während der Transaktion keine Dialoge öffnen. Er merkt
sich Hinweise deshalb nur vor. Sobald Revit wieder im Leerlauf ist
(Idling-Ereignis), erscheinen sie als Sprechblase oben rechts im
Infocenter. Am Dokument wird dabei nichts verändert.
"""

from System import AppDomain, EventHandler
from Autodesk.Revit.UI.Events import IdlingEventArgs

from ga_nachtrag import oberflaeche, projekt, zustand

SCHLUESSEL_LEERLAUF = "GA_Nachtrag.LeerlaufHandler"
TITEL = u"Nachtragsmodus"

_ausstehende_hinweise = []
_uiapp = [None]


def merke_hinweis(text):
    """Merkt einen Hinweis zur Anzeige im nächsten Leerlauf vor."""
    if text not in _ausstehende_hinweise:
        _ausstehende_hinweise.append(text)


def zeige_ausstehende_hinweise():
    while _ausstehende_hinweise:
        zeige_sprechblase(_ausstehende_hinweise.pop(0))


def zeige_sprechblase(text):
    """Zeigt eine Sprechblase (pyRevit), ersatzweise eine Windows-Meldung."""
    from pyrevit import forms
    try:
        forms.show_balloon(TITEL, text)
    except Exception:
        try:
            forms.toast(text, title=TITEL)
        except Exception:
            from pyrevit import script
            script.get_logger().warning(text)


def bei_leerlauf(sender, args):
    """Idling-Handler: zeigt Hinweise und passt den Start-Button an das
    aktive Projekt an (z. B. nach einem Wechsel zwischen Projekten)."""
    try:
        uiapp = _uiapp[0]
        nachtrag = zustand.lies_aktiven_nachtrag(projekt.aktives_projekt(uiapp))
        oberflaeche.aktualisiere_button(uiapp, nachtrag)
        zeige_ausstehende_hinweise()
    except Exception:
        pass  # Ein Hinweis darf Revit nie stören


def abonniere_leerlauf(uiapp):
    """Meldet bei_leerlauf am Idling-Ereignis an.

    Ein Handler aus einem früheren Laden (pyRevit "Reload") wird vorher
    abgemeldet, damit Hinweise nicht doppelt erscheinen.
    """
    alter_handler = AppDomain.CurrentDomain.GetData(SCHLUESSEL_LEERLAUF)
    if alter_handler is not None:
        try:
            uiapp.Idling -= alter_handler
        except Exception:
            pass
    _uiapp[0] = uiapp
    handler = EventHandler[IdlingEventArgs](bei_leerlauf)
    uiapp.Idling += handler
    AppDomain.CurrentDomain.SetData(SCHLUESSEL_LEERLAUF, handler)
