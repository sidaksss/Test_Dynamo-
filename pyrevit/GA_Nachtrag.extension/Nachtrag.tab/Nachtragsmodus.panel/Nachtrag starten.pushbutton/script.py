# -*- coding: utf-8 -*-
"""Nachtrag starten: Nachtragsnummer und Grund abfragen und für diesen
Benutzer aktivieren. Danach platzierte GA-Bauteile werden gekennzeichnet."""

from System.Windows import Visibility

from pyrevit import HOST_APP, forms, script

from ga_nachtrag import oberflaeche, updater, zustand
from ga_nachtrag.eingabe import pruefe_grund, pruefe_nachtragsnummer
from ga_nachtrag.parameter import pruefe_projektparameter


class NachtragDialog(forms.WPFWindow):
    """Dialog mit den Feldern Nachtragsnummer und Grund."""

    def __init__(self, xaml_datei, bisheriger_nachtrag):
        forms.WPFWindow.__init__(self, xaml_datei)
        self.ergebnis = None
        if bisheriger_nachtrag is not None:
            self.Title = u"Nachtrag wechseln"
            self.info_text.Text = (
                u"Aktiv ist Nachtrag {}. Neue Angaben gelten für alle "
                u"danach platzierten GA-Bauteile.".format(
                    bisheriger_nachtrag.nummer))
            self.nummer_feld.Text = str(bisheriger_nachtrag.nummer)
            self.grund_feld.Text = bisheriger_nachtrag.grund
        self.nummer_feld.Focus()

    def starten_klick(self, sender, args):
        nummer, fehler = pruefe_nachtragsnummer(self.nummer_feld.Text)
        if fehler is None:
            grund, fehler = pruefe_grund(self.grund_feld.Text)
        if fehler is not None:
            self.zeige_fehler(fehler)
            return
        self.ergebnis = (nummer, grund)
        self.Close()

    def abbrechen_klick(self, sender, args):
        self.Close()

    def zeige_fehler(self, text):
        self.fehler_text.Text = text
        self.fehler_text.Visibility = Visibility.Visible


def hole_aktives_projekt():
    """Gibt das aktive Projekt zurück oder None (keins offen / Familie)."""
    uidoc = HOST_APP.uiapp.ActiveUIDocument
    if uidoc is None or uidoc.Document.IsFamilyDocument:
        return None
    return uidoc.Document


def pruefe_voraussetzungen(doc):
    """Prüft Projektparameter und Updater. False = nicht starten."""
    pruefung = pruefe_projektparameter(doc)
    if not pruefung.ist_ok:
        forms.alert(
            u"Der Nachtragsmodus kann in diesem Projekt nicht gestartet "
            u"werden. Es wurde nichts geschrieben.",
            sub_msg=u"\n".join(pruefung.fehler + pruefung.hinweise)
            + u"\n\nBitte die Parameter aus GA_Nachtrag_SharedParameters_v2.txt "
            u"als Exemplarparameter für die GA-Kategorien anlegen.",
            title=u"Nachtragsmodus: Parameter fehlen")
        return False
    if pruefung.hinweise:
        if not forms.alert(
                u"Hinweis zu den Projektparametern:",
                sub_msg=u"\n".join(pruefung.hinweise),
                title=u"Nachtragsmodus", ok=False, yes=True, no=True):
            return False
    if not updater.ist_updater_aktiv():
        forms.alert(
            u"Die automatische Kennzeichnung ist nicht aktiv. Der Nachtrag "
            u"wird trotzdem gespeichert, neue Bauteile werden aber erst nach "
            u"einem pyRevit-Reload gekennzeichnet.",
            title=u"Nachtragsmodus", warn_icon=True)
    return True


def frage_nachtrag_ab(bisheriger_nachtrag):
    """Zeigt den Dialog. Rückgabe (nummer, grund) oder None bei Abbruch."""
    dialog = NachtragDialog(script.get_bundle_file("NachtragDialog.xaml"),
                            bisheriger_nachtrag)
    dialog.ShowDialog()
    return dialog.ergebnis


def main():
    doc = hole_aktives_projekt()
    if doc is None:
        forms.alert(u"Bitte zuerst ein Projekt öffnen.", title=u"Nachtragsmodus")
        return
    if not pruefe_voraussetzungen(doc):
        return
    eingabe = frage_nachtrag_ab(zustand.lies_aktiven_nachtrag())
    if eingabe is None:
        return
    nachtrag = zustand.starte_nachtrag(*eingabe)
    oberflaeche.aktualisiere_button(HOST_APP.uiapp, nachtrag)
    forms.alert(
        u"Nachtrag {} ist aktiv.".format(nachtrag.nummer),
        sub_msg=u"Grund: {}\n\nAlle ab jetzt von Ihnen platzierten GA-Bauteile "
                u"erhalten diese Angaben. Die Einstellung gilt nur für Sie, "
                u"nicht für Kollegen im selben Modell.".format(nachtrag.grund),
        title=u"Nachtragsmodus")


try:
    main()
except Exception as fehler:
    forms.alert(u"Beim Starten des Nachtrags ist ein Fehler aufgetreten. "
                u"Es wurde nichts geändert.", sub_msg=str(fehler),
                title=u"Nachtragsmodus", warn_icon=True)
