# Projektzusammenfassung – Dynamo-Automatisierung für LV-Zuordnung und Nachtragserfassung (Revit, Gebäudeautomation)

> Zweck dieser Datei: Kontext für eine KI (z. B. Claude Sonnet), um Prompts zur Weiterentwicklung dieses Projekts zu erzeugen. Stand: Oktober 2026.

---

## 1. Hintergrund

- **Thema (Abschlussarbeit):** „Entwicklung eines Konzepts zur systematischen Nachtragserfassung in BIM-gestützten Gebäudeautomationsprojekten“.
- **Fachgebiet:** Gebäudeautomation (GA), u. a. Siemens-Produkte wie Raumbediengeräte (`QAE2112.010`, `QAM2112.040`), Ventilantriebe (`QAF64.6-J/D`) und Brandmelder (`FDCI222`).
- **Werkzeuge:** Autodesk Revit (deutsche Oberfläche) mit Dynamo **3.6.1**. Python-Knoten laufen mit CPython3 (PythonNet3 soll ebenfalls funktionieren).
- **Repository:** `sidaksss/Test_Dynamo-`, Arbeitsbranch `claude/lucid-mendel-kri0pj`.

### Wichtig über den Anwender

- Der Anwender hat **keine Programmiererfahrung**. Er kann Code weder lesen noch debuggen noch testen.
- Anleitungen müssen deshalb in **kleinstmöglichen Einzelschritten** geschrieben sein: ein Schritt = eine Handlung, auf Deutsch, mit den deutschen Revit-/Dynamo-Menübegriffen.
- Revit läuft auf einem **anderen Rechner** als die KI-Sitzung. Dateien werden über GitHub oder den Chat-Download übertragen.
- Die KI kann Revit **nicht selbst ausführen**. Die Skripte werden nur mit einem simulierten Revit-Modell (Mock) getestet und müssen beim Anwender in echtem Revit geprüft werden.

---

## 2. Aufbau des Repositorys

```
Test_Dynamo-/
├── README.md                          Überblick über das Nachtragskonzept
├── PROJEKT_ZUSAMMENFASSUNG.md         diese Datei
├── shared_parameters/
│   └── GA_Nachtrag_SharedParameters.txt   Freigegebene Parameter (LV_*, Nachtrag_*)
├── dynamo/                            Modul 2: Nachtragserfassung (Konzept)
│   ├── README.md                      Verdrahtung der Knoten, Ablauf je Nachtrag
│   └── python/01_…05_*.py             5 Python-Knoten
└── lv_mapping/                        Modul 1: LV-Nummern-Zuordnung (einsatzbereit)
    ├── LV_Nummer_Zuweisen.dyn         fertiges Dynamo-Skript
    ├── lv_nummer_zuweisen.py          Python-Code des Skripts (lesbare Kopie)
    ├── LV_Datenbank.csv               bereinigte Datenbank
    └── ANLEITUNG.md                   Schritt-für-Schritt-Anleitung für den Anwender
```

---

## 3. Modul 1 – LV-Nummern-Zuordnung (`lv_mapping/`) – aktueller Arbeitsschwerpunkt

### Aufgabe

Jedes Bauteil der gewählten Kategorien bekommt automatisch seine LV-Nummer (Position im Leistungsverzeichnis):

1. Den **Typparameter „Modell“** jedes Bauteiltyps auslesen.
2. Diesen Wert in einer CSV-Datenbank nachschlagen.
3. Die gefundene LV-Nummer in einen **Typparameter** (Standardname `LV_Nummer`) zurückschreiben.
4. Alle Bauteile, die keine LV-Nummer bekommen, in einer Fehlerliste ausgeben.

### Vorgeschichte

Der Anwender hatte zuerst ein eigenes Knoten-Skript gebaut (`BA_LV_Mapping_Test_01.dyn`). Es hatte folgende Fehler:
- `Data.ImportCSV` trennt nur an Kommas, die CSV war aber mit `;` bzw. Tab getrennt.
- Die `in`/`out`-Ausgänge von `List.FilterByBoolMask` waren vertauscht. Dadurch passten zu schreibende Elemente und Werte nicht zusammen, und die Fehlerliste enthielt die gefundenen statt der nicht gefundenen Typen.
- Statt einer Kategorieauswahl waren Element-IDs fest im Skript gespeichert.
- Es gab ungenutzte Knoten.

Deshalb wurde das Skript neu aufgebaut.

### Aufbau des neuen Skripts `LV_Nummer_Zuweisen.dyn`

Das Skript besteht aus nur 4 Knoten:

| Knoten | Art | Funktion |
|---|---|---|
| `1 Datenbank (CSV)` | File Path, als Eingabe markiert | Pfad zur Datenbank |
| `2 Name des LV-Parameters` | String, als Eingabe markiert | Standard `LV_Nummer` |
| `LV-Nummern zuweisen` | Python Script (CPython3) | gesamte Logik |
| `Ergebnis` | Watch, als Ausgabe markiert | Zusammenfassung als Text |

Die Ein- und Ausgaben sind markiert, damit das Skript auch im Dynamo Player läuft.

### Logik des Python-Knotens

1. **Datenbank einlesen:**
   - Trennzeichen `;`, Tab oder `,` werden erkannt.
   - Anführungszeichen, Kopfzeile (`Modell`, `Model`, `Typname`, `Typ`) und Leerzeilen werden ignoriert.
   - Kodierung UTF-8 oder cp1252.
   - Schlüssel werden normalisiert (Großschreibung, Leerzeichen bereinigt), damit der Vergleich tolerant ist.
   - Unlesbare Zeilen und Modelle mit widersprüchlichen LV-Nummern werden gemeldet.
2. **Kategorieauswahl:**
   - Ein Windows-Forms-Fenster (CheckedListBox) zeigt alle Modellkategorien mit Elementen im Modell, jeweils mit Anzahl.
   - Mehrfachauswahl ist möglich. Bei „Abbrechen“ wird nichts geändert.
3. **Verarbeitung:**
   - Erfasst werden alle Exemplare im **ganzen Modell**, die zu den gewählten Kategorien gehören.
   - Jeder Typ wird nur einmal verarbeitet (Cache).
   - „Modell“ wird über `BuiltInParameter.ALL_MODEL_MODEL` gelesen, also sprachunabhängig, mit Rückfall auf `LookupParameter("Modell")`.
   - **Vorhandene LV-Nummern werden nicht überschrieben.**
   - Alle Schreibvorgänge laufen in einer Transaktion. In Revit lässt sich der ganze Lauf mit Strg+Z rückgängig machen.
4. **Fehlerliste:**
   - Datei `LV_Fehlerliste_<Datum>_<Uhrzeit>.csv` auf dem **Desktop**. Der Pfad wird über .NET ermittelt, damit ein OneDrive-Desktop funktioniert.
   - Trennzeichen `;`, Kodierung UTF-8 mit BOM, damit Excel sie direkt öffnet.
   - Spalten: `Element-ID; Modell; Kategorie; Familie; Typ; Grund`. Es gibt eine Zeile pro Exemplar.
   - Mögliche Gründe:
     - `Modell nicht in Datenbank`
     - `Parameter Modell ist leer`
     - `Typparameter '…' fehlt`
     - `… ist kein Text-Parameter`
     - `… ist schreibgeschützt`
     - `Modell steht mehrfach mit unterschiedlichen LV-Nummern in der Datenbank`
     - `Element hat keinen Typ`
     - `Typ nicht gefunden`
     - `Schreiben fehlgeschlagen`
   - Gibt es keine Fehler, wird keine Datei erstellt.
5. **Ausgabe** (Text im Knoten `Ergebnis`):
   - gewählte Kategorien
   - Anzahl geprüfter Elemente und Typen
   - Anzahl der Typen mit neu geschriebener, schon vorhandener bzw. fehlender LV-Nummer
   - Datenbank-Hinweise
   - Pfad der Fehlerliste

### Datenbankformat (`LV_Datenbank.csv`)

```
Modell;LV_Nummer
QAE2112.010;01.01.012
QAF64.6-J/D;01.02.014
QAM2112.040;04.05.200
FDCI222;07.08.820
```

Regeln:
- Genau eine Kopfzeile.
- Spalte 1 = Wert des Revit-Typparameters „Modell“, Spalte 2 = LV-Nummer.
- Einheitliches Trennzeichen `;`.
- Keine Anführungszeichen, keine Leerzeilen.
- Jedes Modell nur einmal.
- Die Datei mit dem Windows-Editor bearbeiten, **nicht mit Excel**. Excel kann LV-Nummern wie `01.02.014` in ein Datum oder eine Zahl umwandeln.

### Status

- **Mock-Tests bestanden:**
  - originale, unsaubere CSV
  - bereinigte CSV
  - Konflikte und unlesbare Zeilen
  - fehlende Datei
  - mehrere Kategorien
  - vorhandene Werte werden nicht überschrieben
- **Noch nicht in echtem Revit getestet.** Rückmeldung des Anwenders steht aus.

### Bekannte Einschränkungen

- Ein Python-Knoten in Dynamo wird beim zweiten Klick auf „Ausführen“ nicht erneut ausgeführt, wenn sich nichts geändert hat. Dann hilft nur Datei schließen und neu öffnen, oder der Dynamo Player.
- Verknüpfte Modelle (Links) werden nicht bearbeitet.
- Die Datenbank wird nur als CSV gelesen, nicht direkt als `.xlsx`.
- Unterschiede zwischen einer vorhandenen LV-Nummer und dem Datenbankwert werden nicht gemeldet.
- Die Fehlerliste ist CSV, nicht `.xlsx`.
- Arbeitsteilung (Worksharing) wird nicht gesondert behandelt, z. B. Typen, die einem anderen Benutzer gehören.

---

## 4. Modul 2 – Nachtragserfassung (`dynamo/`) – Konzept, Grundgerüst

### Ziel

Zwei Modellversionen werden verglichen. Daraus werden je LV-Position Mehrungen und Minderungen ermittelt und ein Teil-Nachtrag als Excel- und PDF-Datei erzeugt.

### Konzept

- **Identifikation:** Elemente werden über die Revit **UniqueId** über Versionen hinweg wiedererkannt.
- **Bewertung je LV-Position**, nicht je Element:
  - `MEHRUNG` bzw. `MINDERUNG`: Die Gesamtstückzahl einer bestehenden Position steigt bzw. sinkt.
  - `NEU_POSITION`: Die Position gab es vorher nicht.
  - `UNVERAENDERT`: keine Änderung.
- **Typwechsel:** Wechselt ein Element seinen Typ und damit die LV-Position, zählt das als Minderung der alten und Mehrung der neuen Position.
- **Baseline:** Ein JSON-Snapshot des vorherigen Nachtrags dient als Vergleichsstand.

### Python-Knoten (`dynamo/python/`)

| Datei | Funktion |
|---|---|
| `01_collect_current_state.py` | Liest pro Element `LV_Positionsnummer`, `LV_Kurztext`, `Basismengeneinheit` und die Menge aus. |
| `02_compare_and_classify.py` | Vergleicht mit dem Baseline-JSON und klassifiziert. |
| `03_write_shared_parameters.py` | Schreibt `Nachtrag_*`-Parameter zurück. |
| `04_build_excel_table.py` | Erzeugt eine 2D-Liste für `Data.ExportExcel` und einen neuen Snapshot. |
| `05_export_pdf_schedule.py` | Erzeugt eine gefilterte Bauteilliste und exportiert sie als PDF. |

### Shared Parameters (`GA_Nachtrag_SharedParameters.txt`)

- LV-Bezug: `LV_Positionsnummer`, `LV_Kurztext`, `Basismengeneinheit`, `Einheitspreis`
- Nachtragsverfolgung: `Nachtrag_ElementGUID`, `Nachtrag_Status`, `Nachtrag_Erstversion`, `Nachtrag_Nummer`, `Nachtrag_Freigabestatus`, `Nachtrag_Bemerkung`

### Status

- Es gibt nur Python-Knoten und eine Verdrahtungsbeschreibung, **keine fertige .dyn-Datei**.
- Nichts davon ist in Revit getestet.

---

## 5. Offene Punkte: Die beiden Module passen noch nicht zusammen

1. **Unterschiedliche Parameternamen:** Modul 1 schreibt nach `LV_Nummer`, Modul 2 liest `LV_Positionsnummer`. Ein einheitlicher Name muss festgelegt werden.
2. **Typ- vs. Exemplarparameter:** Modul 1 schreibt einen **Typparameter**. Modul 2 (`01_collect_current_state.py`) liest mit `el.LookupParameter(...)` am **Exemplar** und findet einen Typparameter deshalb nicht. Modul 2 müsste zusätzlich am Typ nachsehen (`doc.GetElement(el.GetTypeId())`).
3. Modul 2 nutzt noch `ElementId.IntegerValue`. Dieser Wert existiert ab Revit 2026 nicht mehr. Modul 1 verwendet bereits den sicheren Weg über `.Value`.
4. Für Modul 2 fehlt eine fertige `.dyn`-Datei und eine Anleitung für Laien.

---

## 6. Mögliche nächste Entwicklungsschritte (Ideen)

- Die Datenbank zusätzlich als Excel (`.xlsx`) lesen. Sinnvoll ist Spalte 2 als Text formatiert.
- Die Datenbank um `LV_Kurztext` und `Basismengeneinheit` erweitern und diese gleich mit schreiben. Das liefert die Eingangsdaten für Modul 2.
- Einen optionalen Modus „Überschreiben erlauben“ und einen Bericht „vorhandene LV-Nummer weicht von der Datenbank ab“ einbauen.
- Einen Testlauf-Modus anbieten: nur Bericht, nichts schreiben.
- Die Fehlerliste als `.xlsx` ausgeben, gruppiert nach Modell und mit Anzahl der Exemplare, damit fehlende Datenbankeinträge schneller nachgetragen werden können.
- Modul 1 und Modul 2 vereinheitlichen (Parametername, Typ-Lookup) und Modul 2 als einsatzbereite `.dyn` mit Anleitung bauen.
- Den Dynamo Player als Standardweg dokumentieren.

---

## 7. Vorgaben für weitere Entwicklung (bitte in Prompts übernehmen)

- **Sprache:** Antworten und Anleitungen auf Deutsch. Revit-/Dynamo-Menübegriffe in der deutschen Oberfläche.
- **Anleitungen:** kleinstmögliche Einzelschritte, ein Schritt = eine Handlung. Der Anwender ist Laie.
- **Skript-Stil:** möglichst wenige Knoten, Logik in einem Python-Knoten. Ein- und Ausgaben für den Dynamo Player markieren.
- **Python-Code:**
  - kompatibel mit CPython3 und PythonNet3
  - keine f-Strings
  - Einrückung mit Tabs
  - `io.open` mit Kodierung
  - ElementId-Wert über `getattr(id, 'Value', None)` mit Rückfall auf `IntegerValue`
  - BuiltInParameter statt sprachabhängiger Parameternamen, wo möglich
- **Sicherheit:**
  - Vorhandene Werte nicht ungefragt überschreiben.
  - Alle Änderungen in einer Transaktion.
  - Zuerst an einem Testmodell oder einer Sicherheitskopie testen.
- **Ausgaben** für den Anwender auf den Desktop schreiben, mit Zeitstempel im Dateinamen.
- **Testen:** Die KI kann Revit nicht ausführen. Logik mit einem Mock prüfen und klar sagen, dass der Test in Revit beim Anwender noch aussteht.
