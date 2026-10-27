# -*- coding: utf-8 -*-
"""Tests der Eingabeprüfung ohne Revit (Testfall T6 u. a.).

Ausführen im Ordner pyrevit:  python -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                                "GA_Nachtrag.extension", "lib"))

from ga_nachtrag import config  # noqa: E402
from ga_nachtrag.eingabe import (  # noqa: E402
    Nachtrag,
    button_beschriftung,
    dekodiere_nachtrag,
    kodiere_nachtrag,
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


class TestKodierung(unittest.TestCase):

    def test_hin_und_zurueck(self):
        nachtrag = Nachtrag(3, u"Umplanung | Kälte")
        self.assertEqual(dekodiere_nachtrag(kodiere_nachtrag(nachtrag)), nachtrag)

    def test_kein_nachtrag(self):
        self.assertEqual(kodiere_nachtrag(None), u"")
        self.assertIsNone(dekodiere_nachtrag(u""))
        self.assertIsNone(dekodiere_nachtrag(None))

    def test_gespeicherter_aus_zustand(self):
        # So steht ein beendeter Nachtrag in der Benutzerkonfiguration
        self.assertIsNone(dekodiere_nachtrag(u"0|"))

    def test_button_beschriftung(self):
        self.assertEqual(button_beschriftung(Nachtrag(2, u"x")),
                         u"Nachtrag 2\naktiv")
        self.assertEqual(button_beschriftung(None), u"Nachtrag\nstarten")


if __name__ == "__main__":
    unittest.main()
