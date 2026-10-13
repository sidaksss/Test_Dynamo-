# Anleitung: GA-Diagnose ausführen

Das Skript **verändert nichts** an deinem Modell. Es liest nur und legt einen Ordner mit Dateien auf dem Desktop an.

Jeder Schritt enthält genau eine Handlung.

## Teil A – Dateien bereitlegen

1. Gehe an den Rechner mit Revit.
2. Öffne im Browser `https://github.com/sidaksss/Test_Dynamo-/tree/claude/lucid-mendel-kri0pj/konzept/diagnose`.
3. Klicke auf `GA_Diagnose.dyn`.
4. Klicke oben rechts auf den Pfeil nach unten („Download raw file“).
5. Öffne den Windows-Explorer.
6. Öffne den Ordner „Downloads“.
7. Verschiebe `GA_Diagnose.dyn` auf den Desktop.
8. Lege die Datenbank-CSV (`LV_Datenbank.csv`) auf den Desktop. Wenn du keine hast, lass diesen Schritt weg.
9. Exportiere das LV **dieses Projekts** aus SAP als **Excel-Datei (.xlsx)**.
10. Lege die LV-Datei auf den Desktop.
11. Öffne die LV-Datei **nicht** in Excel, um sie zu speichern. Sie muss unverändert bleiben.

## Teil B – Skript öffnen

12. Starte Revit.
13. Öffne das Projektmodell.
14. Klicke auf die Registerkarte „Verwalten“.
15. Klicke auf „Dynamo“.
16. Klicke in Dynamo auf „Öffnen“.
17. Wähle auf dem Desktop `GA_Diagnose.dyn`.
18. Klicke auf „Öffnen“.
19. Du siehst 4 Eingabeblöcke, den Block „GA-Diagnose (nur lesen)“ und den Block „Ergebnis“.

## Teil C – Eingaben einstellen

20. Klicke im Block „1 Datenbank-CSV (optional)“ auf „Durchsuchen…“.
21. Wähle `LV_Datenbank.csv`.
22. Klicke auf „Öffnen“.
23. Klicke im Block „2 LV-Datei aus SAP (optional)“ auf „Durchsuchen…“.
24. Wähle die LV-Datei (.xlsx).
25. Klicke auf „Öffnen“.
26. Prüfe, dass im Block „3 Name eigener LV-Parameter“ `LV_Nummer` steht.
27. Lass den Block „4 Weitere Parameter (kommagetrennt)“ leer.

## Teil D – Ausführen

28. Stelle unten links sicher, dass „Manuell“ ausgewählt ist.
29. Klicke auf „Ausführen“.
30. Warte auf das Fenster „GA-Diagnose (nur lesen)“.
31. Hake **Brandmelder** an.
32. Hake **Sicherheitsgeräte** an.
33. Hake **Datengeräte** an.
34. Hake **Kommunikationsgeräte** an.
35. Hake **Elektrische Ausstattung** an.
36. Hake **HLS-Bauteile** an.
37. Hake **Elektroinstallationen** an.
38. Hake **Notrufgeräte** an.
39. Klicke auf „OK“.
40. Warte. Ein kleines Fenster zeigt den Fortschritt an. Bei rund 20.000 Elementen kann das mehrere Minuten dauern.
41. Warte, bis im Block „Ergebnis“ ein Text erscheint.

## Teil E – Ergebnis ansehen

42. Lies im Block „Ergebnis“ die letzte Zeile. Dort steht der Ordner.
43. Öffne auf dem Desktop den Ordner `GA_Diagnose_<Datum>_<Uhrzeit>`.
44. Doppelklicke auf `1_Kategorien.csv`. Hier siehst du je Kategorie die Kriterien für den Umfang (Siemens-typisch, GA-Funktion, im LV, Kostengruppe, LP8).
45. Doppelklicke auf `7_Filter.csv`. Die Spalte „Regeln“ zeigt, nach welchem Parameter die Ausblend-Filter arbeiten.
46. Doppelklicke auf `6_Verknuepfungen.csv`. Hier siehst du, ob GA-Bauteile in verknüpften Modellen liegen.

## Teil F – Ergebnis an mich zurückgeben

47. Prüfe, ob die Dateien vertrauliche Daten enthalten. `5a` und `5c` enthalten LV-Mengen, aber keine Preise.
48. Hänge `0_Zusammenfassung.txt`, `1_Kategorien.csv`, `3_Parameter.csv`, `6_Verknuepfungen.csv`, `7_Filter.csv`, `8_Werte.csv` und `9_Verschachtelung.csv` an deine nächste Nachricht an.
49. Hänge `2_Kombinationen.csv`, `4_Modell_fehlt_in_DB.csv` und die `5`-Dateien an, wenn das erlaubt ist.

## Wenn etwas nicht klappt

| Was du siehst | Was du tust |
|---|---|
| Der Block „GA-Diagnose“ wird gelb oder rot. | Mit der Maus darauf zeigen, Meldung fotografieren, mir schicken. |
| Kein Fortschrittsfenster. | Nicht schlimm. Einfach warten, bis im Block „Ergebnis“ Text steht. |
| Die `5`-Dateien fehlen. | Es wurde keine LV-Datei angegeben (Schritte 23–25). |
| Erneut ausführen geht nicht. | Datei in Dynamo schließen und neu öffnen. |
