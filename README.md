# Entwicklung eines Konzepts zur systematischen Nachtragserfassung in BIM-gestützten Gebäudeautomationsprojekten

Prototypische Umsetzung eines Dynamo-Graphen, der zwischen zwei
Versionen eines Revit-Modells Mehrungen und Minderungen je Bauteil der
Gebäudeautomation erkennt und daraus einen Teil-Nachtrag als Excel- und
PDF-Datei erzeugt.

## Inhalt

- `shared_parameters/GA_Nachtrag_SharedParameters.txt` – Freigegebene
  Parameter für LV-Bezug und Nachtragsverfolgung (siehe unten).
- `dynamo/python/` – Python-Script-Nodes für den Dynamo-Graphen
  (Versionsvergleich, Klassifikation, Rückschreiben der Parameter,
  Excel-/PDF-Export).
- `dynamo/README.md` – Verdrahtung der Knoten im Dynamo-Graphen und
  Ablaufbeschreibung je Nachtrag.
- `shared_parameters/GA_Nachtrag_SharedParameters_v2.txt` – Parameter
  `NT_*` für den Nachtragsmodus und die Auswertung.
- `pyrevit/` – pyRevit-Erweiterung „Nachtragsmodus“: kennzeichnet neu
  platzierte GA-Bauteile automatisch mit Nachtragsnummer und Grund
  (siehe `pyrevit/README.md`, Testfälle in `pyrevit/TESTANLEITUNG.md`).

## Konzept in Kürze

**Erkennung:** Elemente werden über ihre Revit Unique Id versionsübergreifend
identifiziert. Mehrung/Minderung wird **je LV-Position** ermittelt, nicht je
Einzelelement:

- LV-Position existierte bereits und die Gesamtstückzahl steigt/sinkt →
  `MEHRUNG` / `MINDERUNG`.
- LV-Position taucht erstmals auf (keine Vorgänger-Menge) → `NEU_POSITION`,
  im Nachtrag separat hervorgehoben statt als Mehrung gewertet.
- Ein Bauteil bleibt (gleiche Unique Id), wechselt aber Typ/Parameter und
  damit die LV-Position → wird als Minderung der alten und
  Mehrung/Neu-Position der neuen LV-Position abgebildet.
- Reine Positions-/Ortsänderung ohne LV-Wechsel → keine Nachtragsrelevanz.

**Shared Parameter** (Details siehe Datei): `LV_Positionsnummer`,
`LV_Kurztext`, `Basismengeneinheit`, `Nachtrag_ElementGUID`,
`Nachtrag_Status`, `Nachtrag_Erstversion`, `Nachtrag_Nummer`,
`Nachtrag_Freigabestatus`, `Nachtrag_Bemerkung`, optional `Einheitspreis`.

**Ausgabe:** Je Nachtrag (`Nachtrag 1`, `Nachtrag 2`, …) eine Excel-Datei
mit LV-Positionsnummer, Basismengeneinheit, Stückzahl dieses Nachtrags,
kumulierter Gesamtstückzahl und Kurztext, sowie eine PDF-Datei aus einem
gefilterten Revit-Zeitplan mit Nachweis-Metadaten und Freigabestatus-Feld.
