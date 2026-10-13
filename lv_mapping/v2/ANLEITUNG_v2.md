# Anleitung: LV-Zuordnung v2

Diese Fassung erweitert dein erstes Skript (`lv_mapping/LV_Nummer_Zuweisen.dyn`). Das erste Skript bleibt unverändert.

## Was das Skript macht

Für jedes Bauteil der gewählten Kategorien prüft das Skript nacheinander:

| Stufe | Prüfung | Ergebnis |
|---|---|---|
| 0 | LV-Nummer schon eingetragen? | bleibt, wird **nie überschrieben** |
| 1 | „Modell“ oder Typname steht in deiner **Datenbank-CSV** | **sicher** |
| 2 | „Modell“ = Leistungsnummer, L-Identifizierer oder Materialnummer im **SAP-LV** | **sicher**, wenn nur eine LV-Position passt |
| 3 | Leistungsnummer aus dem SAP-LV steckt im Typ- oder Familiennamen | **sicher**, wenn nur eine LV-Position passt |
| 4 | **Ähnlichkeitssuche:** alle Textparameter des Bauteils gegen Leistungsnummer, Hersteller-Typ und Kurztext im SAP-LV | nur **Vorschlag** mit Punktzahl, wird **nie** automatisch geschrieben |

- Geschrieben wird nur bei **sicheren** Treffern, und nur wenn der Schalter „4 In Modell schreiben“ auf `True` steht.
- Planerparameter (`ZWP_…`) werden nicht gelesen.

**Ergebnisordner** auf dem Desktop: `LV_Zuordnung_<Datum>_<Uhrzeit>`

| Datei | Inhalt |
|---|---|
| `1_Ergebnis_je_Bauteil.csv` | jedes Bauteil mit Element-ID, Modell, LV-Nummer, Status und Grund |
| `2_Vorschlaege.csv` | **eine Zeile je Kombination** mit bis zu 3 Vorschlägen, Punktzahl und LV-Kurztext; Spalte 2 ist leer und für deine Entscheidung gedacht |
| `3_Copilot_Anfrage.txt` | fertiger Text für Copilot mit allen offenen Kombinationen und ihren LV-Kandidaten (ohne Preise) |
| `4_Schreibfehler.csv` | nur, wenn etwas nicht geschrieben werden konnte (z. B. Bauteil belegt) |

Bewertung der Punktzahl **[Annahme, nach den ersten Läufen anpassen]**:
- ab 0,75 „stark“
- ab 0,5 „mittel“
- darunter „schwach“
- unter 0,2 gibt es keinen Vorschlag

Status „mehrdeutig“ heißt: Das Produkt steht in mehreren LV-Positionen, z. B. in mehreren Abschnitten. Welche gilt, entscheidest du.

---

## Teil A – Dateien bereitlegen

1. Öffne im Browser `https://github.com/sidaksss/Test_Dynamo-/tree/claude/lucid-mendel-kri0pj/lv_mapping/v2`.
2. Klicke auf `LV_Zuordnung_v2.dyn`.
3. Klicke oben rechts auf den Pfeil nach unten („Download raw file“).
4. Verschiebe die Datei aus „Downloads“ auf den Desktop.
5. Exportiere das LV aus SAP als **Excel-Datei (.xlsx)**.
6. Lege die LV-Datei auf den Desktop. Öffne und speichere sie **nicht** in Excel.
7. Lege deine Datenbank-CSV auf den Desktop (Aufbau wie bisher: `Modell;LV_Nummer`).

## Teil B – Erster Lauf als Test

8. Öffne in Revit dein Projekt.
9. Klicke auf „Verwalten“.
10. Klicke auf „Dynamo“.
11. Klicke auf „Öffnen“.
12. Wähle `LV_Zuordnung_v2.dyn` auf dem Desktop.
13. Klicke im Block „1 SAP-LV (.xlsx)“ auf „Durchsuchen…“.
14. Wähle die LV-Datei.
15. Klicke im Block „2 Datenbank-CSV“ auf „Durchsuchen…“.
16. Wähle deine Datenbank-CSV.
17. Prüfe im Block „3 Zielparameter“, dass dort der Name deines LV-Parameters steht (z. B. `LV_Nummer`).
18. Prüfe, dass im Block „4 In Modell schreiben“ **False** ausgewählt ist. Das ist der Testlauf.
19. Stelle unten links „Manuell“ ein.
20. Klicke auf „Ausführen“.
21. Hake im Fenster die Kategorien an.
22. Klicke auf „OK“.
23. Warte, bis im Block „Ergebnis“ Text erscheint.
24. Lies die Zahlen: sicher zugeordnet, Vorschlag, offen.

## Teil C – Vorschläge prüfen (Datenbank pflegen)

25. Öffne den Ergebnisordner auf dem Desktop.
26. Doppelklicke auf `2_Vorschlaege.csv`.
27. Lies in einer Zeile den Vorschlag 1 und den LV-Kurztext dazu.
28. Passt der Vorschlag, trage die LV-Nummer in Spalte 2 („LV-Nummer (hier bestätigen)“) ein.
29. Passt keiner, lass Spalte 2 leer.
30. Wiederhole die Schritte 27–29 für alle Zeilen.
31. Markiere alle Zeilen, in denen Spalte 2 ausgefüllt ist.
32. Kopiere die Spalten 1 und 2 dieser Zeilen (Strg + C).
33. Öffne deine Datenbank-CSV mit dem **Editor**.
34. Gehe ans Ende der Datei.
35. Füge die Zeilen ein (Strg + V).
36. Ersetze dabei den Tabulator zwischen den beiden Werten durch ein Semikolon `;`. Der Editor hilft mit „Bearbeiten“ → „Ersetzen“.
37. Speichere mit Strg + S.

Ab dem nächsten Lauf gelten diese Zeilen als **sicher**. Jede Entscheidung pflegst du also **nur einmal**.

## Teil D – Optional: Copilot fragen

38. Öffne `3_Copilot_Anfrage.txt`.
39. Markiere den ganzen Text (Strg + A).
40. Kopiere ihn (Strg + C).
41. Öffne Copilot.
42. Füge den Text ein (Strg + V) und sende ihn ab.
43. Lies die Antwort. Copilot liefert je Schlüssel eine LV-Nummer und eine Begründung.
44. Prüfe jede Zeile **selbst**. Übernimm nur, was du fachlich bestätigst, so wie in Teil C ab Schritt 31.

## Teil E – Schreiben

45. Stelle im Block „4 In Modell schreiben“ auf **True** um. Weil sich eine Eingabe geändert hat, läuft das Skript beim nächsten Klick neu.
46. Klicke auf „Ausführen“.
47. Hake die Kategorien an und klicke auf „OK“.
48. Prüfe in Revit an einem Bauteil, ob die LV-Nummer eingetragen ist.
49. Falls etwas falsch ist: Drücke in Revit Strg + Z. Der ganze Lauf wird rückgängig gemacht.

## Hinweise

- Ist der Zielparameter ein **Typparameter**, schreibt das Skript nur, wenn alle Bauteile dieses Typs dieselbe LV-Nummer bekommen. Sonst steht der Typ in `4_Schreibfehler.csv`.
- Bei Produkten, die in **mehreren** LV-Positionen stehen, kann ein einziger Datenbank-Eintrag (Modell → LV-Nummer) nur eine Position abbilden. Für solche Fälle gibt es später die Abschnitts-Tabelle aus dem Konzept (Kapitel 5.3).
- Getestet ist das Skript nur mit Beispieldaten. **Der Test in echtem Revit steht aus.** Wenn ein Block gelb oder rot wird: Meldung fotografieren und mir schicken.
