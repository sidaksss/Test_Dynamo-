# pyRevit-Erweiterung „Nachtragsmodus“ (GA_Nachtrag)

Das Planungsteam schaltet vor dem Modellieren eines Nachtrags den
Nachtragsmodus ein. Danach erhält jedes **neu platzierte GA-Bauteil**
automatisch `NT_Nachtragsnummer` und `NT_Grund`. Die Auswertung
(Vertragsstand, LV-Zuordnung, Mengen, Export) übernehmen die Dynamo-Skripte.

Zielumgebung: Revit 2026, pyRevit 6.5.5, IronPython-Engine (Standard).

## Installation

1. Voraussetzung im Projekt: `NT_Nachtragsnummer` und `NT_Grund` aus
   `shared_parameters/GA_Nachtrag_SharedParameters_v2.txt` als
   **Exemplarparameter** für die GA-Kategorien anlegen
   (Verwalten → Projektparameter). Die GUIDs müssen aus dieser Datei stammen.
2. Ordner `pyrevit` aus diesem Repository lokal ablegen,
   z. B. `C:\Users\<Name>\GA_Nachtrag\pyrevit`.
3. In Revit: pyRevit → Einstellungen → *Custom Extension Directories* →
   den Ordner `pyrevit` (der `GA_Nachtrag.extension` enthält) hinzufügen →
   Speichern → **Reload**. Adminrechte sind nicht nötig.
4. Es erscheint der Reiter **Nachtrag** mit der Gruppe **Nachtragsmodus**.

Die Kategorienliste und weitere Einstellungen stehen in
`GA_Nachtrag.extension/lib/ga_nachtrag/config.py`. Nach Änderungen: Reload.

## Bedienung

| Button | Wirkung |
|---|---|
| **Nachtrag starten** | Dialog: Nachtragsnummer (nur Ziffern, > 0) und Grund (Pflicht, max. 100 Zeichen). Prüft vorher die Projektparameter. Der Nachtrag gilt nur für das **aktive Projekt**. Danach zeigt der Button „Nachtrag 2 aktiv“, ein grünes Symbol und im Tooltip den Grund. Erneutes Klicken wechselt den Nachtrag. |
| **Nachtrag beenden** | Schaltet den Modus im aktiven Projekt aus. Der Button zeigt wieder „Nachtrag starten“. |

Automatisch im Hintergrund:

- **Modus aktiv:** neue GA-Bauteile (auch Kopien) erhalten Nummer und Grund
  des aktiven Nachtrags.
- **Modus aus:** neue GA-Bauteile bleiben leer. Kopien, die Werte vom
  Original geerbt haben, werden geleert. Sie gelten als möglicher
  Vertragsstand.
- **Löschen von GA-Bauteilen:** Hinweis oben rechts (Infocenter):
  „Bauteile nicht löschen, sondern als entfallen markieren. Rückgängig mit
  Strg+Z.“ Am Modell wird dabei nichts verändert.

Der aktive Nachtrag gilt **nur für den eigenen Benutzer** und ist an die
**Projektdatei** gebunden, in der er gestartet wurde:

- Jedes Projekt hat seinen eigenen Zustand. Nachtrag 2 in Projekt A und
  Nachtrag 5 in Projekt B können gleichzeitig aktiv sein. In einem Projekt
  ohne gestarteten Nachtrag ist der Modus aus.
- Erkannt wird die Projektdatei im Worksharing am Pfad des
  **Zentralmodells**. Eine neu erstellte lokale Kopie gehört also zum selben
  Projekt. Ohne Worksharing zählt der Dateipfad, bei Cloud-Modellen der
  Cloud-Pfad.
- Der Button zeigt immer den Zustand des gerade aktiven Projekts und
  wechselt beim Umschalten zwischen offenen Projekten mit.
- Ein nie gespeichertes Projekt hat noch keine Datei; dort lässt sich kein
  Nachtrag starten.

Gespeichert wird in der pyRevit-Benutzerkonfiguration
(`%APPDATA%\pyRevit\pyRevit_config.ini`, Abschnitt `GA_Nachtrag`, Option
`aktive_nachtraege`), nicht im Modell. Der Zustand bleibt nach einem
Neustart von Revit erhalten.

Strg+Z nach dem Platzieren nimmt Bauteil und Kennzeichnung gemeinsam zurück,
weil der Updater in derselben Transaktion schreibt.

## Aufbau

```
pyrevit/
├── GA_Nachtrag.extension/
│   ├── startup.py                     Registriert Updater + Hinweise beim Laden
│   ├── lib/ga_nachtrag/
│   │   ├── config.py                  GA-Kategorien, GUIDs, Einstellungen
│   │   ├── eingabe.py                 Eingabeprüfung (ohne Revit testbar)
│   │   ├── projekt.py                 projektschluessel (Bindung an Projektdatei)
│   │   ├── zustand.py                 lies_aktiven_nachtrag, starte/beende_nachtrag
│   │   ├── parameter.py               pruefe_projektparameter, Parameterzugriff
│   │   ├── kennzeichnung.py           kennzeichne_bauteile
│   │   ├── updater.py                 NachtragsUpdater (IUpdater), Registrierung
│   │   ├── hinweise.py                Nicht blockierende Hinweise (Idling)
│   │   └── oberflaeche.py             Beschriftung/Symbol des Start-Buttons
│   └── Nachtrag.tab/Nachtragsmodus.panel/
│       ├── Nachtrag starten.pushbutton/   script.py, NachtragDialog.xaml, Symbole
│       └── Nachtrag beenden.pushbutton/   script.py, icon.png
├── tests/test_eingabe.py              Unit-Tests ohne Revit
└── TESTANLEITUNG.md                   Testfälle T1–T10 in Revit
```

## Wahl der Python-Engine: IronPython 2.7 (pyRevit-Standard)

- Eine IronPython-Klasse kann das .NET-Interface `IUpdater` direkt
  implementieren. Das Objekt ist ein gewöhnliches .NET-Objekt, das Revit
  dauerhaft hält und aus der Transaktion heraus aufruft.
- In CPython (pythonnet) braucht eine Klasse, die ein .NET-Interface
  implementiert, Sonderangaben (`__namespace__`). Jeder Aufruf aus Revit muss
  zusätzlich in den Python-Interpreter wechseln. pyRevit weist darauf hin,
  dass Ereignisse und langlebige Objekte unter CPython nur eingeschränkt
  unterstützt sind. Ein Updater, den Revit nach einem Reload noch aufruft,
  wäre ein Absturzrisiko.
- `startup.py`, Ereignis-Handler und `forms.WPFWindow` sind in pyRevit mit
  IronPython am besten erprobt. Die Erweiterung braucht keine
  CPython-Pakete (numpy o. Ä.).

## Technische Umsetzung (Kurzfassung)

- **Updater**: `UpdaterRegistry.RegisterUpdater(updater, True)`, also
  optional. Wer das Modell ohne pyRevit öffnet, bekommt keine Warnung.
  Trigger: `Element.GetChangeTypeElementAddition()` und
  `…ElementDeletion()`, jeweils mit `ElementMulticategoryFilter`
  (GA-Kategorien) UND `ElementIsElementTypeFilter(True)` (nur Exemplare).
- **Schreiben**: nur `NT_Nachtragsnummer` und `NT_Grund` (über die GUID
  gesucht), nur innerhalb der laufenden Transaktion des Updaters. Kein
  Löschen, keine Änderung an Geometrie, Typen oder anderen Parametern.
- **Zustand**: Gespeichert wird eine Zuordnung Projektdatei → Nachtrag
  (JSON). Die Buttons schreiben in die pyRevit-Benutzerkonfiguration
  und zusätzlich in den AppDomain-Speicher von Revit. Der Updater liest aus
  dem AppDomain-Speicher, weil jeder pyRevit-Button in einer eigenen
  Python-Umgebung läuft.
- **Hinweise**: Der Updater öffnet keine Dialoge. Er merkt Hinweise vor,
  angezeigt werden sie im nächsten `Idling`-Ereignis als Sprechblase.
- **Worksharing**: Bauteile, die einem anderen Benutzer gehören, werden
  nicht verändert. Die Fehler werden gesammelt und gemeldet. Mit
  `NUR_EIGENE_BAUTEILE_KENNZEICHNEN = True` (Standard) werden nur Bauteile
  gekennzeichnet, die dem aktuellen Benutzer gehören. Neu erstellte Bauteile
  gehören bis zur Synchronisierung ihrem Ersteller, Bauteile von Kollegen
  bleiben also unverändert (T10).
- **Nicht** über den pyRevit-Hook `doc-changed`, weil das Dokument im
  `DocumentChanged`-Ereignis nicht verändert werden darf.

## Bekannte Grenzen

- Erkannt wird nur das **Hinzufügen** von Bauteilen. Typwechsel oder
  Parameteränderungen an bestehenden Bauteilen werden nicht gekennzeichnet
  (geplant: Stufe 2 „Bauteil zuordnen“).
- Wird ein Projekt unter neuem Namen oder Pfad gespeichert, verschoben oder
  als neues Zentralmodell abgelegt, gilt es als andere Projektdatei. Der
  Nachtrag muss dort neu gestartet werden.
- Laufen zwei Revit-Sitzungen gleichzeitig, wirkt Starten oder Beenden nur in
  der Sitzung, in der geklickt wurde. Die andere übernimmt den Stand erst
  nach Neustart oder Reload.
- Kollegen **ohne pyRevit** kennzeichnen nichts. Ihre Kopien von
  Nachtragsbauteilen behalten die Werte des Originals.
- Beim Leeren nutzt die Erweiterung `Parameter.ClearValue()`, sofern die
  Revit-API die Methode anbietet. Sonst wird `NT_Nachtragsnummer = 0`
  geschrieben. Die Auswertung muss „leer“ und „0“ gleich behandeln.
- Beim Platzieren von **Modellgruppen** werden auch die enthaltenen
  GA-Bauteile gekennzeichnet. Dafür sollte bei den Projektparametern
  „Werte können je nach Gruppeninstanz variieren“ aktiv sein.
- Der Löschhinweis erscheint auch, wenn Revit GA-Bauteile indirekt löscht
  (z. B. zusammen mit ihrem Host).
- Werte können in der Eigenschaften-Palette weiterhin von Hand überschrieben
  werden.
