# -*- coding: utf-8 -*-
"""Schreiben von NT_Nachtragsnummer und NT_Grund an neue GA-Bauteile.

Wird vom Updater innerhalb der laufenden Revit-Transaktion aufgerufen.
Es werden ausschließlich diese beiden Parameter geschrieben; Geometrie,
Typen und andere Parameter bleiben unverändert, es wird nichts gelöscht.
"""

from Autodesk.Revit.DB import CheckoutStatus, WorksharingUtils

from ga_nachtrag import config
from ga_nachtrag.parameter import hole_nachtragsparameter, hat_passenden_speichertyp


class Kennzeichnungsergebnis(object):
    """Sammelt, was beim Kennzeichnen passiert ist (für Hinweise)."""

    def __init__(self):
        self.gekennzeichnet = 0
        self.geleert = 0
        self.ohne_parameter = set()   # Kategorienamen ohne NT-Parameter
        self.nicht_im_besitz = 0      # Worksharing: nicht eigene Bauteile
        self.fehler = []              # Fehlertexte je Bauteil


def kennzeichne_bauteile(doc, element_ids, nachtrag):
    """Kennzeichnet neu hinzugefügte Bauteile.

    nachtrag gesetzt: Nummer und Grund des aktiven Nachtrags schreiben.
    nachtrag None:    Nummer und Grund leeren (z. B. bei kopierten
                      Bauteilen, die sonst die Werte des Originals erben).
    Fehler werden gesammelt, die Verarbeitung läuft weiter.
    """
    ergebnis = Kennzeichnungsergebnis()
    for element_id in element_ids:
        try:
            _kennzeichne_ein_bauteil(doc, element_id, nachtrag, ergebnis)
        except Exception as fehler:
            ergebnis.fehler.append(u"Bauteil {}: {}".format(element_id, fehler))
    return ergebnis


def _kennzeichne_ein_bauteil(doc, element_id, nachtrag, ergebnis):
    element = doc.GetElement(element_id)
    if element is None:
        return

    parameter_nummer, parameter_grund = hole_nachtragsparameter(element)
    if parameter_nummer is None or parameter_grund is None:
        ergebnis.ohne_parameter.add(_kategoriename(element))
        return

    if not darf_bauteil_bearbeiten(doc, element_id, ergebnis):
        return

    if parameter_nummer.IsReadOnly or parameter_grund.IsReadOnly:
        ergebnis.fehler.append(
            u"Bauteil {}: Parameter ist schreibgeschützt.".format(element_id))
        return
    if not hat_passenden_speichertyp(parameter_nummer, parameter_grund):
        ergebnis.fehler.append(
            u"Bauteil {}: NT-Parameter haben einen falschen Datentyp."
            .format(element_id))
        return

    if nachtrag is not None:
        setze_nachtragswerte(parameter_nummer, parameter_grund, nachtrag)
        ergebnis.gekennzeichnet += 1
    elif leere_nachtragswerte(parameter_nummer, parameter_grund):
        ergebnis.geleert += 1


def darf_bauteil_bearbeiten(doc, element_id, ergebnis):
    """Worksharing: Bauteile anderer Benutzer werden nicht verändert."""
    if not doc.IsWorkshared:
        return True
    status = WorksharingUtils.GetCheckoutStatus(doc, element_id)
    if status == CheckoutStatus.OwnedByOtherUser:
        ergebnis.fehler.append(
            u"Bauteil {}: von einem anderen Benutzer belegt.".format(element_id))
        return False
    if (status == CheckoutStatus.NotOwned
            and config.NUR_EIGENE_BAUTEILE_KENNZEICHNEN):
        ergebnis.nicht_im_besitz += 1
        return False
    return True


def setze_nachtragswerte(parameter_nummer, parameter_grund, nachtrag):
    """Schreibt Nummer und Grund des aktiven Nachtrags."""
    if not parameter_nummer.HasValue or parameter_nummer.AsInteger() != nachtrag.nummer:
        parameter_nummer.Set(int(nachtrag.nummer))
    if parameter_grund.AsString() != nachtrag.grund:
        parameter_grund.Set(nachtrag.grund)


def leere_nachtragswerte(parameter_nummer, parameter_grund):
    """Leert Nummer und Grund. Gibt True zurück, wenn etwas geändert wurde.

    Ein neu platziertes Bauteil ist ohnehin leer und wird nicht angefasst.
    Ein kopiertes Bauteil hat die Werte des Originals geerbt; dann wird die
    Nummer geleert (bzw. auf 0 gesetzt, falls Leeren nicht möglich ist) und
    der Grund auf einen leeren Text gesetzt.
    """
    geaendert = False
    if parameter_nummer.HasValue and parameter_nummer.AsInteger() != 0:
        _leere_ganzzahl(parameter_nummer)
        geaendert = True
    if parameter_grund.AsString():
        parameter_grund.Set(u"")
        geaendert = True
    return geaendert


def _leere_ganzzahl(parameter):
    # Parameter.ClearValue entfernt den Wert ganz ("leer"). Falls die
    # Methode nicht verfügbar ist oder scheitert, wird 0 geschrieben.
    leeren = getattr(parameter, "ClearValue", None)
    if leeren is not None:
        try:
            leeren()
            return
        except Exception:
            pass
    parameter.Set(0)


def _kategoriename(element):
    kategorie = element.Category
    return kategorie.Name if kategorie is not None else u"(ohne Kategorie)"
