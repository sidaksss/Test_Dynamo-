# -*- coding: utf-8 -*-
"""Tests der Eingabeprüfung ohne Revit (Testfall T6 u. a.).

Ausführen im Ordner pyrevit:  python -m unittest discover tests
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "GA_Nachtrag.extension", "lib"))

from ga_nachtrag import config  # noqa: E402
from ga_nachtrag.eingabe import (  # noqa: E402
    Nachtrag,
    button_beschriftung,
    dekodiere_nachtraege,
    kodiere_nachtraege,
    normalisiere_projektschluessel,
    pruefe_grund,
    pruefe_nachtragsnummer,
)


class TestNachtragsnummer(unittest.TestCase):

    def test_gueltige_nummer(self):
        self.assertEqual(pruefe_nachtragsnummer(u"2"), (2, None))
        self.assertEqual(pruefe_nachtragsnummer(u" 12 "), (12, None))

    def test_t6_buchstaben_werden_abgelehnt(self):
        nummer, fehler = pruefe_nachtragsnummer(u"N2")
        self.assertIsNone(nummer)
        self.assertIn(u"Ziffern", fehler)

    def test_t6_null_wird_abgelehnt(self):
        nummer, fehler = pruefe_nachtragsnummer(u"0")
        self.assertIsNone(nummer)
        self.assertIn(u"größer als 0", fehler)

    def test_weitere_ungueltige_eingaben(self):
        for text in [u"", u"   ", None, u"-1", u"+2", u"2.0", u"2,0",
                     u"2a", u"1 2", u"２", u"00"]:
            nummer, fehler = pruefe_nachtragsnummer(text)
            self.assertIsNone(nummer, text)
            self.assertTrue(fehler, text)

    def test_zu_grosse_nummer(self):
        self.assertIsNone(pruefe_nachtragsnummer(u"2147483648")[0])
        self.assertEqual(pruefe_nachtragsnummer(u"2147483647")[0], 2147483647)


class TestGrund(unittest.TestCase):

    def test_gueltiger_grund(self):
        self.assertEqual(pruefe_grund(u"  Zusätzliche Fühler EG  "),
                         (u"Zusätzliche Fühler EG", None))

    def test_pflichtfeld(self):
        self.assertIsNone(pruefe_grund(u"")[0])
        self.assertIsNone(pruefe_grund(u"   ")[0])
        self.assertIsNone(pruefe_grund(None)[0])

    def test_zu_lang(self):
        self.assertIsNone(pruefe_grund(u"x" * (config.MAX_LAENGE_GRUND + 1))[0])
        self.assertIsNotNone(pruefe_grund(u"x" * config.MAX_LAENGE_GRUND)[0])

    def test_nur_eine_zeile(self):
        self.assertIsNone(pruefe_grund(u"Zeile 1\nZeile 2")[0])


class TestProjektbindung(unittest.TestCase):

    def test_hin_und_zurueck(self):
        nachtraege = {
            u"c:/projekte/a/zentral.rvt": Nachtrag(3, u"Umplanung | Kälte"),
            u"c:/projekte/b/zentral.rvt": Nachtrag(5, u"Zusätzliche Fühler"),
        }
        self.assertEqual(dekodiere_nachtraege(kodiere_nachtraege(nachtraege)),
                         nachtraege)

    def test_umlaute_nur_ascii_gespeichert(self):
        # Fehler aus Revit: "'unknown' codec can't decode byte 0xc4 in
        # position 3" bei einem "Ä" an Stelle 3. Der gespeicherte Text muss
        # deshalb reines ASCII sein und trotzdem alles zurückliefern.
        nachtraege = {
            u"c:/projekte/änderungen/a.rvt": Nachtrag(2, u"GA Änderung Fühler"),
            u"c:/b.rvt": Nachtrag(7, u'Zitat "x" \\ Pfad, Größe \U0001F600'),
        }
        text = kodiere_nachtraege(nachtraege)
        text.encode("ascii")  # wirft einen Fehler, falls nicht ASCII
        self.assertEqual(dekodiere_nachtraege(text), nachtraege)
        self.assertEqual(json.loads(text)[u"c:/b.rvt"][u"nummer"], 7)

    def test_leer(self):
        self.assertEqual(kodiere_nachtraege({}), u"{}")
        self.assertEqual(dekodiere_nachtraege(u""), {})
        self.assertEqual(dekodiere_nachtraege(None), {})
        self.assertEqual(dekodiere_nachtraege(u"kein json"), {})

    def test_bereits_als_dict_gelesen(self):
        # pyRevit liefert JSON-Texte aus der Konfiguration ggf. schon als dict
        self.assertEqual(dekodiere_nachtraege({u"x": {u"nummer": 2, u"grund": u"g"}}),
                         {u"x": Nachtrag(2, u"g")})

    def test_ungueltige_eintraege_entfallen(self):
        text = (u'{"a": {"nummer": 0, "grund": "g"}, "b": {"nummer": 2, "grund": ""},'
                u' "c": "kaputt", "d": {"nummer": 4, "grund": "ok"}}')
        self.assertEqual(dekodiere_nachtraege(text), {u"d": Nachtrag(4, u"ok")})

    def test_projektschluessel(self):
        self.assertEqual(
            normalisiere_projektschluessel(u"\\\\Server\\GA\\Zentral.RVT"),
            u"//server/ga/zentral.rvt")
        self.assertEqual(normalisiere_projektschluessel(u"C:\\Projekte\\A.rvt"),
                         normalisiere_projektschluessel(u"c:/projekte/a.rvt"))
        self.assertIsNone(normalisiere_projektschluessel(u""))
        self.assertIsNone(normalisiere_projektschluessel(None))

    def test_button_beschriftung(self):
        self.assertEqual(button_beschriftung(Nachtrag(2, u"x")),
                         u"Nachtrag 2\naktiv")
        self.assertEqual(button_beschriftung(None), u"Nachtrag\nstarten")


if __name__ == "__main__":
    unittest.main()
