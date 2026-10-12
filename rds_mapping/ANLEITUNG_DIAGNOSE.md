# Anleitung: RDS-Diagnose ausführen

Das Diagnose-Skript **verändert nichts** an deinem Modell. Es liest nur und schreibt drei CSV-Dateien auf den Desktop.

Jeder Schritt enthält genau eine Handlung.

## Teil A – Datei holen

1. Gehe an den Rechner mit Revit.
2. Öffne im Browser `https://github.com/sidaksss/Test_Dynamo-/tree/claude/lucid-mendel-kri0pj/rds_mapping/prototypen`.
3. Klicke auf `RDS_Diagnose.dyn`.
4. Klicke oben rechts auf den Pfeil nach unten („Download raw file“).
5. Öffne den Windows-Explorer.
6. Öffne den Ordner „Downloads“.
7. Verschiebe `RDS_Diagnose.dyn` auf den Desktop.

## Teil B – Skript öffnen

8. Starte Revit.
9. Öffne das Projekt, das du untersuchen willst.
10. Klicke auf die Registerkarte „Verwalten“.
11. Klicke auf „Dynamo“.
12. Klicke in Dynamo auf „Öffnen“.
13. Wähle auf dem Desktop `RDS_Diagnose.dyn`.
14. Klicke auf „Öffnen“.

## Teil C – Optional: weitere Parameter

15. Schau in den Block „Weitere Parameter (kommagetrennt)“.
16. Lass ihn leer, wenn dir die Standardliste reicht.
17. Willst du zusätzliche Parameter sehen: Tippe ihre Namen mit Komma getrennt ein, z. B. `Hersteller_Artikel, Mein_Parameter`.

## Teil D – Ausführen

18. Stelle unten links sicher, dass „Manuell“ ausgewählt ist.
19. Klicke auf „Ausführen“.
20. Warte auf das Fenster „RDS-Diagnose (nur lesen)“.
21. Hake die Kategorien an, die du untersuchen willst (z. B. die GA-Kategorien).
22. Klicke auf „OK“.
23. Warte, bis im Block „Ergebnis“ ein Text erscheint. Bei großen Modellen kann das einige Minuten dauern.

## Teil E – Ergebnis

24. Lies im Block „Ergebnis“ die Kernzahlen.
25. Lies in der letzten Zeile, wo der Ergebnisordner liegt.
26. Öffne auf dem Desktop den Ordner `RDS_Diagnose_<Datum>_<Uhrzeit>`.
27. Doppelklicke auf `3_Parameter.csv`.
28. Sieh nach, in welcher Spalte bei `RDS_Code` die größte Zahl steht: „nur Exemplar“ oder „nur Typ“. Das beantwortet die Frage, wo die RDS-Parameter liegen.
29. Doppelklicke auf `2_Typen.csv`.
30. Sieh in der Spalte „Anzahl versch. RDS-Typschluessel“ nach. Eine `1` heißt: Alle Exemplare dieses Typs haben dieselbe RDS-Funktion.

## Teil F – Ergebnis an mich zurückgeben

31. Prüfe, ob die Dateien vertrauliche Daten enthalten, die nicht weitergegeben werden dürfen.
32. Hänge `2_Typen.csv` und `3_Parameter.csv` an deine nächste Nachricht an.
33. Hänge `1_Elemente.csv` nur an, wenn das erlaubt ist.

> Wenn ein Block gelb oder rot wird: Zeige mit der Maus darauf, fotografiere die Meldung und schick sie mir.
>
> Zum erneuten Ausführen: Datei in Dynamo schließen und neu öffnen.
