# Dynamo-Graph: Teil-Nachtragserfassung GA

Dieser Graph vergleicht den aktuellen Modellstand gegen den Snapshot der
letzten Nachtragserfassung, klassifiziert jede LV-Position als
`NEU_POSITION`, `MEHRUNG`, `MINDERUNG` oder `UNVERAENDERT`, schreibt das
Ergebnis in die Shared Parameter zurück und exportiert Excel- und
PDF-Nachtragslisten.

## Voraussetzung: Shared Parameters laden

`shared_parameters/GA_Nachtrag_SharedParameters.txt` über
*Verwalten → Freigegebene Parameter* laden und alle `Nachtrag_*`- sowie
`LV_*`-Parameter den relevanten GA-Kategorien (Mechanische Ausrüstung /
MSR-Geräte, Elektrogeräte / Schaltschränke, Kabelverlegungen) als
Projektparameter zuordnen. `LV_Positionsnummer`, `LV_Kurztext` und
`Basismengeneinheit` werden im Zuge der LV-Zuordnung händisch bzw. aus dem
LV importiert befüllt, bevor der Graph läuft.

## Knotenkette

0a. **`00a_list_unique_geraetebezeichnungen.py`** *(eigenständiges Hilfsskript,
    nicht Teil der Nachtrags-Pipeline)*
   Durchsucht eine Elementliste über das **gesamte Projekt** (keine
   View-Einschränkung) und liefert eine **duplikatfreie, alphabetisch
   sortierte Liste** der Werte aus dem Parameter `GERAETEBEZEICHNUNG`; ist
   dieser bei einem Element leer, wird ersatzweise `Modell` verwendet
   (Fallback). Beide Parameter werden sowohl auf der Instanz als auch auf
   dem Elementtyp gesucht, da `Modell` bei vielen Familien ein
   Typparameter ist. Gedacht als Ausgangsliste für eine eigene
   (Dummy-)Datenbank, z. B. als Vorstufe zur LV-Zuordnung.
   - **Auswahl** – OOTB-Nodes `Categories` (Mehrfachauswahl der
     gewünschten GA-Kategorien) + `All Elements of Category`, zu einer
     flachen Liste zusammengeführt (`List.Flatten`) → Python-Node **IN[0]**.
   - Input: `elements`, optional `primary_param_name` (String Input,
     Default `GERAETEBEZEICHNUNG`), `fallback_param_name` (String Input,
     Default `Modell`).
   - Output: `[unique_values, skipped]` – `unique_values` ist die fertige
     Liste (z. B. an `Watch` oder `Data.ExportExcel` anschließen),
     `skipped` listet die Element-IDs, bei denen beide Parameter leer
     waren (zur Vollständigkeitskontrolle).

0. **`00_lv_zuordnung_by_typ.py`** *(optionaler Vorlauf-Schritt)*
   Ordnet Bauteilen der **aktiven Ansicht** anhand des Shared Parameters
   `Typ` (z. B. `QMX2.P33`) automatisch die passende `LV Nummer` aus einer
   Excel-Tabelle zu. Nützlich, um `LV_Positionsnummer` (bzw. hier `LV
   Nummer`) vor dem eigentlichen Nachtrags-Lauf ohne Handarbeit zu befüllen.
   - **Excel einlesen** – OOTB-Node `Excel.ReadFromFile` (Datei, Blattname,
     `readAsStrings = true`) liefert eine 2D-Liste inkl. Kopfzeile. Die
     Tabelle hat genau zwei Spalten: **Spalte 1 = `LV Nummer`**,
     **Spalte 2 = `Typ`**. Alternativ `Data.ImportCSV`, falls kein Excel
     installiert ist (dann Datei vorher als CSV speichern).
   - Input: `excel_rows` (2D-Liste aus dem Excel-Node), `typ_param_name`
     (String Input, Default `Typ`), `lv_param_name` (String Input, Default
     `LV Nummer`), `ask_before_overwrite` (Boolean Input, Default `true`).
   - Verhalten: Elemente ohne beide Parameter werden übersprungen. Ist
     `LV Nummer` bereits mit einem *anderen* Wert befüllt, erscheint pro
     Konflikt ein Ja/Nein-Dialog ("vorhandenen Wert überschreiben?"). Wird
     zu `Typ` kein Eintrag in der Excel-Liste gefunden, erscheint am Ende
     eine Sammelmeldung mit allen betroffenen Element-IDs.
   - Output: `[updated, not_found, declined]` – je eine Log-Liste zur
     Kontrolle (z. B. per `Watch`-Node).
   - Voraussetzung: `Typ` und `LV Nummer` sind als (Shared-)Projektparameter
     den relevanten Kategorien zugeordnet (siehe
     `shared_parameters/GA_Nachtrag_SharedParameters.txt`, Gruppe
     *LV-Zuordnung*).
1. **Auswahl** – `Categories` + `All Elements of Category` (OOTB) für die
   drei GA-Kategorien, zusammengeführt zu einer flachen Elementliste.
2. **`01_collect_current_state.py`**
   Input: Elementliste, Name des Mengenparameters (String, leer = jedes
   Element zählt als 1 Stk).
   Output: `[records, skipped]` – `records` ist eine Liste von Dicts pro
   Element, `skipped` listet Elemente ohne `LV_Positionsnummer` (diese
   werden bewusst nicht Teil des Nachtrags, solange sie nicht dem LV
   zugeordnet sind).
3. **Eingabeknoten** (String Input / Filename): `baseline_json_path`
   (Pfad zum JSON-Snapshot des vorherigen Nachtrags, leer beim allerersten
   Lauf), `current_version_label` (z. B. `V3`), `nachtrag_nummer` (z. B.
   `Nachtrag 3`).
4. **`02_compare_and_classify.py`**
   Input: `records` aus Schritt 2, `baseline_json_path`,
   `current_version_label`, `nachtrag_nummer`.
   Output: `[position_summary, element_updates, entfallene_elemente,
   current_records]`.
5. **`03_write_shared_parameters.py`**
   Input: `element_updates`, Default-Freigabestatus (String, z. B.
   `offen`).
   Schreibt `Nachtrag_ElementGUID`, `Nachtrag_Status`,
   `Nachtrag_Erstversion`, `Nachtrag_Nummer` und – falls noch leer –
   `Nachtrag_Freigabestatus` auf jedes betroffene Element.
6. **`04_build_excel_table.py`**
   Input: `position_summary`, `nachtrag_nummer`, `erstellungsdatum`
   (String Input, z. B. aus `DateTime.Now`), `modellversion`,
   `current_records`, Pfad für den nächsten Snapshot
   (`Nachtrag_<n>_snapshot.json`).
   Output: 2D-Liste, direkt an **`Data.ExportExcel`** (OOTB) anschließen →
   `Nachtrag_<n>.xlsx`.
7. **`05_export_pdf_schedule.py`**
   Input: `nachtrag_nummer`, Kategorie-Schlüssel (`MSR_Geraete` /
   `Schaltschraenke` / `Kabeltrassen`), Zielordner, Dateiname.
   Legt bei Bedarf einen gefilterten Zeitplan `Nachtrag_<n>` an (Filter
   `Nachtrag_Nummer = <n>`) und exportiert ihn nativ als
   `Nachtrag_<n>.pdf`.

## Ablauf je Nachtrag

1. Modell auf den gewünschten Stand bringen (Version B).
2. Pfad zum JSON-Snapshot der letzten Version als `baseline_json_path`
   angeben (beim ersten Nachtrag leer lassen).
3. Graph ausführen → Shared Parameter werden gesetzt, Excel + PDF werden
   erzeugt, neuer Snapshot `Nachtrag_<n>_snapshot.json` wird geschrieben.
4. Diesen Snapshot als `baseline_json_path` für den nächsten Nachtrag
   verwenden.

## Bekannte Grenzen / mögliche Erweiterungen

- Element-Matching erfolgt über die Revit *Unique Id*; wird ein Bauteil
  gelöscht und als neues Element neu erzeugt (statt Typ zu wechseln), wird
  es als `MINDERUNG` (altes Element) + `NEU_ELEMENT`/`MEHRUNG` (neues
  Element) erfasst – inhaltlich korrekt, aber ohne automatische
  Verknüpfung als "Austauschpaar". Eine räumliche Zuordnung (z. B. über
  `Location`-Distanz) wäre eine sinnvolle Erweiterung für die Diskussion
  in der Arbeit.
- Preisspalte (`Einheitspreis`) ist im Shared-Parameter-Set vorbereitet,
  aber noch nicht in `04_build_excel_table.py` verrechnet – bei Bedarf
  einfach `Stueckzahl_Nachtrag * Einheitspreis` ergänzen.
- Für optische Hervorhebung der `NEU_POSITION`-Zeilen in Excel (Farbe) statt
  nur als separater Block: `Excel.WriteToFile` (Package *Rhythm* /
  *archilab*) mit Zellformatierung statt `Data.ExportExcel` verwenden.
