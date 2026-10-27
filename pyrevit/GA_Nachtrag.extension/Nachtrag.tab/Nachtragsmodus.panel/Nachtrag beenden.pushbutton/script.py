# -*- coding: utf-8 -*-
"""Nachtrag beenden: Nachtragsmodus für diesen Benutzer ausschalten."""

from pyrevit import HOST_APP, forms

from ga_nachtrag import oberflaeche, zustand


def main():
    nachtrag = zustand.lies_aktiven_nachtrag()
    zustand.beende_nachtrag()
    oberflaeche.aktualisiere_button(HOST_APP.uiapp, None)
    if nachtrag is None:
        forms.alert(u"Es ist kein Nachtrag aktiv.", title=u"Nachtragsmodus")
        return
    forms.alert(
        u"Nachtrag {} ist beendet.".format(nachtrag.nummer),
        sub_msg=u"Ab jetzt platzierte GA-Bauteile erhalten keine "
                u"Nachtragsnummer und keinen Grund und gelten als möglicher "
                u"Vertragsstand. Bereits gekennzeichnete Bauteile bleiben "
                u"unverändert.",
        title=u"Nachtragsmodus")


try:
    main()
except Exception as fehler:
    forms.alert(u"Beim Beenden des Nachtrags ist ein Fehler aufgetreten.",
                sub_msg=str(fehler), title=u"Nachtragsmodus", warn_icon=True)
