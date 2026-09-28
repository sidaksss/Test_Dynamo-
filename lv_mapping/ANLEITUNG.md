# Anleitung: LV-Nummern mit Dynamo zuweisen

Jeder Schritt enthält genau eine Handlung. Arbeite die Schritte der Reihe nach ab.

## Die drei Dateien

| Datei | Wofür |
|---|---|
| `LV_Nummer_Zuweisen.dyn` | Das Dynamo-Skript. Diese Datei öffnest du in Dynamo. |
| `LV_Datenbank.csv` | Die bereinigte Datenbank (Spalte 1 = Modell, Spalte 2 = LV-Nummer). |
| `lv_nummer_zuweisen.py` | Der Python-Code zum Nachlesen. Er steckt bereits in der .dyn-Datei. Du brauchst diese Datei nicht. |

---

## Teil A – Dateien auf den Revit-Rechner holen

1. Gehe an den Rechner, auf dem Revit installiert ist.
2. Öffne dort einen Internetbrowser (z. B. Edge oder Chrome).
3. Öffne diese Adresse: `https://github.com/sidaksss/Test_Dynamo-/tree/claude/lucid-mendel-kri0pj/lv_mapping`
4. Melde dich bei GitHub an, falls du dazu aufgefordert wirst.
5. Klicke in der Dateiliste auf `LV_Nummer_Zuweisen.dyn`.
6. Klicke oben rechts auf das Symbol mit dem Pfeil nach unten („Download raw file“).
7. Gehe im Browser einen Schritt zurück zur Dateiliste.
8. Klicke auf `LV_Datenbank.csv`.
9. Klicke wieder auf das Symbol mit dem Pfeil nach unten.
10. Öffne den Windows-Explorer.
11. Öffne links den Ordner „Downloads“.
12. Prüfe, dass dort beide Dateien liegen.
13. Markiere beide Dateien.
14. Schneide sie aus (Strg + X).
15. Öffne links den Ordner „Desktop“.
16. Füge die Dateien dort ein (Strg + V).

> Alternativ: Öffne auf dem Revit-Rechner diese Unterhaltung auf claude.ai und lade die Dateien über die Dateikarten herunter. Danach weiter mit Schritt 10.

---

## Teil B – Datenbank prüfen

17. Klicke auf dem Desktop mit der rechten Maustaste auf `LV_Datenbank.csv`.
18. Wähle „Öffnen mit“.
19. Wähle „Editor“ (nicht Excel – siehe Hinweis unten).
20. Prüfe, dass die erste Zeile `Modell;LV_Nummer` lautet.
21. Prüfe, dass jede weitere Zeile so aussieht: `Modellname;LV-Nummer`.
22. Füge bei Bedarf weitere Zeilen im gleichen Muster hinzu (eine Zeile pro Modell).
23. Speichere mit Strg + S.
24. Schließe den Editor.

> **Warum nicht Excel?** Excel verwandelt LV-Nummern wie `01.02.014` beim Speichern manchmal in ein Datum oder eine Zahl. Der Editor lässt den Text unverändert.

---

## Teil C – Revit vorbereiten

25. Starte Revit.
26. Öffne dein Projekt.
27. Speichere eine Sicherheitskopie oder arbeite beim ersten Mal in einem Testmodell.
28. Klicke auf ein Bauteil, das eine LV-Nummer bekommen soll.
29. Klicke in der Eigenschaftenpalette auf „Typ bearbeiten“.
30. Suche in der Liste den Parameter „Modell“.
31. Prüfe, dass dort ein Wert steht, der in deiner Datenbank vorkommt.
32. Suche in der gleichen Liste den Parameter für die LV-Nummer.
33. Merke dir den genauen Namen dieses Parameters (z. B. `LV_Nummer`).
34. Schließe das Fenster mit „Abbrechen“.

---

## Teil D – Skript in Dynamo öffnen

35. Klicke in Revit auf die Registerkarte „Verwalten“.
36. Klicke ganz rechts auf „Dynamo“.
37. Warte, bis das Dynamo-Fenster erscheint.
38. Klicke in Dynamo auf „Öffnen“.
39. Wähle links „Desktop“.
40. Wähle `LV_Nummer_Zuweisen.dyn`.
41. Klicke auf „Öffnen“.
42. Du siehst jetzt 4 Blöcke: „1 Datenbank (CSV)“, „2 Name des LV-Parameters“, „LV-Nummern zuweisen“ und „Ergebnis“.

---

## Teil E – Eingaben einstellen

43. Klicke im Block „1 Datenbank (CSV)“ auf „Durchsuchen…“.
44. Wähle auf dem Desktop `LV_Datenbank.csv`.
45. Klicke auf „Öffnen“.
46. Schau in den Block „2 Name des LV-Parameters“.
47. Prüfe, dass dort genau der Name aus Schritt 33 steht.
48. Falls nicht: Klicke in das Textfeld.
49. Lösche den alten Text.
50. Tippe den richtigen Namen ein (Groß-/Kleinschreibung beachten).

---

## Teil F – Skript ausführen

51. Schau unten links im Dynamo-Fenster nach der Auswahl „Manuell“ / „Automatisch“.
52. Stelle sicher, dass „Manuell“ ausgewählt ist.
53. Klicke unten links auf „Ausführen“.
54. Warte, bis das Fenster „LV-Nummern zuweisen“ erscheint (es kann einige Sekunden dauern).
55. Hake die Kategorien an, deren Bauteile eine LV-Nummer bekommen sollen.
56. Klicke auf „OK“.
57. Warte, bis im Block „Ergebnis“ ein Text erscheint.

---

## Teil G – Ergebnis lesen

58. Lies im Block „Ergebnis“ die Zeile „LV-Nummer neu geschrieben“.
59. Lies die Zeile „LV-Nummer war schon vorhanden“. Diese Typen wurden absichtlich nicht verändert.
60. Lies die Zeile „Ohne LV-Nummer“.
61. Lies die letzte Zeile. Dort steht, wo die Fehlerliste gespeichert wurde.

---

## Teil H – Ergebnis in Revit kontrollieren

62. Wechsle zu Revit.
63. Klicke auf ein Bauteil aus einer der gewählten Kategorien.
64. Klicke auf „Typ bearbeiten“.
65. Prüfe, dass im LV-Parameter jetzt die LV-Nummer steht.
66. Schließe das Fenster mit „Abbrechen“.

> Wenn etwas falsch geschrieben wurde: Drücke in Revit Strg + Z. Damit wird der ganze Dynamo-Lauf rückgängig gemacht.

---

## Teil I – Fehlerliste öffnen

67. Gehe zum Desktop.
68. Suche die Datei `LV_Fehlerliste_<Datum>_<Uhrzeit>.csv`.
69. Doppelklicke darauf. Sie öffnet sich in Excel.
70. Du siehst die Spalten: Element-ID, Modell, Kategorie, Familie, Typ und Grund.
71. Lies in der Spalte „Grund“, warum ein Bauteil keine LV-Nummer bekommen hat.

Bedeutung der Gründe:

| Grund | Was du tun kannst |
|---|---|
| Modell nicht in Datenbank | Das Modell als neue Zeile in `LV_Datenbank.csv` eintragen. |
| Parameter Modell ist leer | Im Revit-Typ den Parameter „Modell“ ausfüllen. |
| Typparameter '…' fehlt | Den LV-Parameter dieser Kategorie als Typparameter zuordnen. |
| Modell steht mehrfach mit unterschiedlichen LV-Nummern in der Datenbank | In der Datenbank eine der doppelten Zeilen löschen. |
| Element hat keinen Typ | Diese Kategorie beim nächsten Mal nicht anhaken. |

Ein bestimmtes Bauteil aus der Liste in Revit finden:

72. Kopiere die Element-ID aus Excel.
73. Klicke in Revit auf „Verwalten“.
74. Klicke im Bereich „Abfrage“ auf „Auswahl nach ID“ (je nach Version heißt der Knopf „Nach ID auswählen“).
75. Füge die ID ein.
76. Klicke auf „Anzeigen“.

> Falls Excel alles in eine einzige Spalte schreibt: Spalte A markieren → „Daten“ → „Text in Spalten“ → „Getrennt“ → „Semikolon“ anhaken → „Fertig stellen“.

---

## Teil J – Skript ein zweites Mal ausführen

77. Ergänze die fehlenden Modelle in der Datenbank (Teil B).
78. Schließe die Datei in Dynamo.
79. Öffne sie erneut (Teil D).
80. Klicke auf „Ausführen“ (Teil F).

> Dynamo führt Blöcke, die sich nicht geändert haben, beim zweiten Klick auf „Ausführen“ nicht erneut aus. Deshalb Datei schließen und neu öffnen.

---

## Wenn etwas nicht funktioniert

| Was du siehst | Was du tust |
|---|---|
| Im Block „Ergebnis“ steht `FEHLER: Datenbank-Datei nicht gefunden` | Schritte 43–45 wiederholen. |
| Der Block „LV-Nummern zuweisen“ ist gelb oder rot | Mit der Maus auf den Block zeigen, den Text abfotografieren und mir schicken. |
| Das Kategorie-Fenster erscheint nicht | In der Windows-Taskleiste nachsehen, ob es hinter Revit liegt. |
| Warnung zur Python-Engine am Block „LV-Nummern zuweisen“ | Doppelklick auf den Block → unten die Engine „CPython3“ oder „PythonNet3“ wählen → „Speichern“ → erneut ausführen. |
