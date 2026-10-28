# -*- coding: utf-8 -*-
"""Nachtrag starten: Nachtragsnummer und Grund abfragen und für diesen
Benutzer im aktiven Projekt aktivieren. Danach in diesem Projekt platzierte
GA-Bauteile werden gekennzeichnet."""

from pyrevit import HOST_APP, forms, script

from ga_nachtrag import oberflaeche, updater, zustand
from ga_nachtrag.projekt import aktives_projekt, projektschluessel
from ga_nachtrag.eingabe import pruefe_grund, pruefe_nachtragsnummer
from ga_nachtrag.parameter import pruefe_projektparameter


class NachtragDialog(forms.WPFWindow):
    """Dialog mit den Feldern Nachtragsnummer und Grund."""

    def __init__(self, xaml_datei, projektname, bisheriger_nachtrag):
        forms.WPFWindow.__init__(self, xaml_datei)
        self.ergebnis = None
        self.info_text.Text = (
            u"Projekt: {}\nAlle danach in diesem Projekt neu platzierten "
            u"GA-Bauteile erhalten diese Angaben automatisch."
            .format(projektname))
        if bisheriger_nachtrag is not None:
            self.Title = u"Nachtrag wechseln"
            self.info_text.Text = (
                u"Projekt: {}\nAktiv ist Nachtrag {}. Neue Angaben gelten "
                u"für alle danach platzierten GA-Bauteile.".format(
                    projektname, bisheriger_nachtrag.nummer))
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
        # Das Textfeld ist immer da, aber leer, solange kein Fehler vorliegt
        self.fehler_text.Text = text


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


def frage_nachtrag_ab(doc, bisheriger_nachtrag):
    """Zeigt den Dialog. Rückgabe (nummer, grund) oder None bei Abbruch."""
    dialog = NachtragDialog(script.get_bundle_file("NachtragDialog.xaml"),
                            doc.Title, bisheriger_nachtrag)
    dialog.ShowDialog()
    return dialog.ergebnis


def main():
    doc = aktives_projekt(HOST_APP.uiapp)
    if doc is None:
        forms.alert(u"Bitte zuerst ein Projekt öffnen.", title=u"Nachtragsmodus")
        return
    if projektschluessel(doc) is None:
        forms.alert(u"Bitte das Projekt zuerst speichern.",
                    sub_msg=u"Der Nachtrag wird an die Projektdatei gebunden. "
                            u"Ein nie gespeichertes Projekt hat noch keine.",
                    title=u"Nachtragsmodus")
        return
    if not pruefe_voraussetzungen(doc):
        return
    eingabe = frage_nachtrag_ab(doc, zustand.lies_aktiven_nachtrag(doc))
    if eingabe is None:
        return
    nummer, grund = eingabe
    nachtrag = zustand.starte_nachtrag(doc, nummer, grund)
    oberflaeche.aktualisiere_button(HOST_APP.uiapp, nachtrag)
    forms.alert(
        u"Nachtrag {} ist im Projekt '{}' aktiv.".format(nachtrag.nummer,
                                                         doc.Title),
        sub_msg=u"Grund: {}\n\nAlle ab jetzt von Ihnen in diesem Projekt "
                u"platzierten GA-Bauteile erhalten diese Angaben. Andere "
                u"Projekte und Kollegen im selben Modell sind nicht "
                u"betroffen.".format(nachtrag.grund),
        title=u"Nachtragsmodus")


try:
    main()
except Exception as fehler:
    forms.alert(u"Beim Starten des Nachtrags ist ein Fehler aufgetreten. "
                u"Es wurde nichts geändert.", sub_msg=str(fehler),
                title=u"Nachtragsmodus", warn_icon=True)
