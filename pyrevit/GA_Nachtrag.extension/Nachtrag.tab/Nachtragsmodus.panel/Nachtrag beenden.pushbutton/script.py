# -*- coding: utf-8 -*-
"""Nachtrag beenden: Nachtragsmodus für diesen Benutzer im aktiven Projekt
ausschalten."""

from pyrevit import HOST_APP, forms

from ga_nachtrag import oberflaeche, zustand
from ga_nachtrag.projekt import aktives_projekt


def main():
    doc = aktives_projekt(HOST_APP.uiapp)
    if doc is None:
        forms.alert(u"Bitte zuerst ein Projekt öffnen.", title=u"Nachtragsmodus")
        return
    nachtrag = zustand.lies_aktiven_nachtrag(doc)
    if nachtrag is None:
        forms.alert(u"Im Projekt '{}' ist kein Nachtrag aktiv.".format(doc.Title),
                    title=u"Nachtragsmodus")
        return
    zustand.beende_nachtrag(doc)
    oberflaeche.aktualisiere_button(HOST_APP.uiapp, None)
    forms.alert(
        u"Nachtrag {} ist im Projekt '{}' beendet.".format(nachtrag.nummer,
                                                           doc.Title),
        sub_msg=u"Ab jetzt in diesem Projekt platzierte GA-Bauteile erhalten "
                u"keine Nachtragsnummer und keinen Grund und gelten als "
                u"möglicher Vertragsstand. Bereits gekennzeichnete Bauteile "
                u"bleiben unverändert.",
        title=u"Nachtragsmodus")


try:
    main()
except Exception as fehler:
    forms.alert(u"Beim Beenden des Nachtrags ist ein Fehler aufgetreten.",
                sub_msg=str(fehler), title=u"Nachtragsmodus", warn_icon=True)
