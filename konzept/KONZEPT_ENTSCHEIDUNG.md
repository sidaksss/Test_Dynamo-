# Konzeptentscheidung: Zuordnung Revit-Bauteile → Leistungsverzeichnis und Nachtragsauswertung

> **Zweck:** Die Konzeptphase abschließen und **ein** Konzept festlegen. Hier wird noch nichts Endgültiges gebaut.
>
> **Grundlagen:**
> - `PROJEKT_ZUSAMMENFASSUNG.md`
> - `rds_mapping/MACHBARKEIT_RDS_LV.md`
> - `rds_mapping/DIAGNOSE_AUSWERTUNG_1.md` (echte Daten, 10.882 Elemente)
> - der SAP-Beispielexport
> - deine Antworten auf die 10 Fragen
>
> **Kennzeichnung im Text:**
> - **[Befund]**: aus echten Daten belegt.
> - **[Annahme]**: plausibel, aber nicht belegt. Schwellenwerte sind immer Annahmen.
> - **[Offen]**: braucht eine Antwort (Kapitel 11).
>
> **Status des Diagnose-Skripts** `konzept/diagnose/GA_Diagnose.dyn`: nur mit simulierten Daten (Mock) getestet. **Der Test in echtem Revit steht bei dir aus.**

---

## 0. Die Entscheidung

> **Empfohlen wird Weg C, die Kaskade, aber in der Reihenfolge „Modell zuerst“. RDS dient nur zur Plausibilitätsprüfung und als Ortsangabe, nicht als Schlüssel.**
>
> Jede menschliche Entscheidung wird **genau einmal** in einer Tabelle gespeichert und danach bei jedem Lauf und jedem Nachtrag automatisch wiederverwendet.

**Begründung in fünf Sätzen:**

1. „Modell“ ist bei den Siemens-Produkten zu ≈ 100 % gefüllt und enthält die Produktbezeichnung, also genau den Wert der SAP-Spalte `Leistungsnummer`. **[Befund + deine Antwort 4]**
2. Das RDS taugt nicht als Schlüssel zum LV:
   - Ein RDS-Schlüssel passt bei 30 % der Elemente zu **mehreren** Produkten.
   - Ein Produkt hat bis zu 10 verschiedene RDS-Schlüssel. **[Befund]**
   - Das LV enthält kein RDS. **[deine Antwort 3]**
3. Für Bauteile ohne „Modell“ (Generikfamilien, Trassen) ist der **Typname** der bessere Schlüssel. Die Zuordnung dafür wird einmal in einer kleinen Tabelle gepflegt. Eine KI kann einmalig Vorschläge machen.
4. Kommt ein Produkt in mehreren LV-Abschnitten vor, entscheidet ein Mensch **einmal je Kombination aus Produkt und Anlage**, nicht je Bauteil. Eine Regel dafür gibt es nicht. **[deine Antwort 1]**
5. So wird jede Information nur einmal gepflegt, wie du es forderst. Mehrfachpflege, die das Konzept fehleranfällig machen würde, entsteht nicht.

---

## 1. Begriffe in einem Satz

| Begriff | Bedeutung |
|---|---|
| **LV** | Leistungsverzeichnis; die verbindliche Liste der beauftragten Leistungen mit Positionsnummer, Menge, Einheit und Preis. |
| **Leistungsnummer** | SAP-Spalte; bei Produkten die Produktbezeichnung (z. B. `QAM2112.040`), bei Pauschalen ein Code (z. B. `DL_Z501`). |
| **LV-Position** | Ordnungszahl im LV, z. B. `04.01.01.20` (SAP-Spalte `ext. Leistungsnummer`). |
| **Masterposition / Unterposition** | Eine Master-Position (`M`) fasst mehrere Unterpositionen (`U`) zusammen. Abgerechnet werden kann auch nur ein Teil davon. |
| **Exemplar / Typ** | Jedes einzelne Bauteil im Modell ist ein Exemplar. Der Typ ist die gemeinsame „Bauart“ mehrerer Exemplare. |
| **RDS** | Referenzkennzeichen nach IEC 81346: Ort (`+`), System (`#`), Funktion (`=`). |
| **Kaskade** | Feste Reihenfolge von Prüfungen; die erste, die sicher trifft, gewinnt. |
| **Kombination** | Eindeutige Zusammenstellung aus Kategorie, Familie, Typ, Modell und RDS-Teilen. Viele Bauteile teilen sich eine Kombination, und entschieden wird je Kombination. |
| **UniqueId** | Dauerhafte Kennung eines Bauteils in Revit, die über Modellstände hinweg gleich bleibt. Die kurze Element-ID ist dafür nicht gedacht. |
| **Worksharing / Arbeitssatz** | Mehrere Personen arbeiten gleichzeitig im Modell. Wer ein Bauteil gerade „belegt“, darf es ändern, alle anderen nicht. |
| **Verknüpfung (Link)** | Ein anderes Revit-Modell, das nur eingeblendet ist. Seine Bauteile kann man lesen, aber aus dem offenen Modell heraus **nicht** ändern. |

---

## 2. Was wir schon wissen

| Nr. | Aussage | Quelle |
|---|---|---|
| W1 | Die RDS-Parameter sind **Exemplar**parameter. | Diagnose 1 [Befund] |
| W2 | „Modell“ ist bei Siemens-Produktfamilien zu 1.321 von 1.322 gefüllt, bei Generikfamilien und Trassen zu 0. | Diagnose 1 [Befund] |
| W3 | „Modell“ enthält die Produktbezeichnung, nicht die Bestellnummer. | deine Antwort 4 |
| W4 | RDS-Schlüssel (System \| Funktion) → Produkt ist nur für 882 von 1.253 Elementen (70 %) eindeutig. | Diagnose 1 [Befund] |
| W5 | Ein Produkt kommt im LV in mehreren Positionen vor (Beispiel-LV: jedes Produkt 6–7-mal). Eine Regel RDS → LV-Abschnitt gibt es nicht. | SAP-Beispiel [Befund], deine Antwort 1 |
| W6 | Das LV enthält kein RDS und keinen Langtext. | deine Antworten 2, 3 |
| W7 | 69 Elemente sind verschachtelte Unterfamilien („UF“) → Gefahr der Doppelzählung. | Diagnose 1 [Befund]; ob sie wirklich verschachtelt sind, prüft die neue Diagnose |
| W8 | `ZWP_…`-Parameter gehören dem Planer und werden **nur gelesen**. `ZWP_400_LP8_Abrechnung` war in Diagnose 1 **nirgends** gesetzt. | deine Vorgabe, Diagnose 1 |
| W9 | Masterpositionen können teilweise (nur einzelne Unterpositionen) im Nachtrag landen. | deine Antwort 8 |
| W10 | Bei Siemens ist Copilot freigegeben, darin ist Claude nutzbar. | deine Antwort 9 |
| W11 | Eine Fachperson kann ~50 Fälle von Hand prüfen, aber nicht 500. | deine Antwort 10 |

---

## 3. Gehört zu einem RDS-Schlüssel genau eine LV-Position? – Nein.

Belegt mit drei Ketten:

1. **RDS → Produkt ist mehrdeutig. [Befund]**
   - `HZK|BTAR` steht im Modell für drei verschiedene Fühler (`QAE2112.010`, `QAE2112.015`, `QAD2012`).
   - Das sind drei verschiedene LV-Positionen.
2. **Produkt → LV-Position ist mehrdeutig. [Befund, SAP-Beispiel]**
   - Dasselbe Produkt steht in mehreren LV-Abschnitten.
3. **Es gibt keine Regel RDS → Abschnitt. [deine Antwort 1]**

**Folge:** RDS allein (Weg B) ist als Schlüssel zum LV **nicht zuverlässig**. RDS bleibt nützlich:
- als **Plausibilitätsprüfung** (passt die Funktion zum Produkt?),
- als **Anlagenangabe** für die einmalige Abschnittsentscheidung (Kapitel 5.3).

---

## 4. Die drei Wege im Vergleich

| Kriterium | **A) Modell-first** (wie heute) | **B) RDS-first** + KI | **C) Kaskade, Modell zuerst** (empfohlen) |
|---|---|---|---|
| Aufwand | gering | hoch: RDS-Tabelle, KI-Prüfschleife | mittel |
| Zuverlässigkeit | hoch für Siemens-Produkte, **0 %** für Bauteile ohne Modell | **niedrig**: 30 % mehrdeutig (W4), kein RDS im LV (W6) | hoch: jede Stufe hat ein festes Vertrauen, Unsicheres geht auf die Prüfliste |
| Wartbarkeit | gut, wenn die Datenbank aus dem SAP-LV kommt statt von Hand | schlecht: Tabelle wächst mit jeder Anlage | gut: drei kleine Tabellen, jede Entscheidung nur einmal |
| Datenschutz | sehr gut (keine KI) | KI nötig | KI nur optional, einmalig, ohne Preise |
| Abdeckung in Diagnose 1 | ca. 12 % der Elemente (nur Siemens-Produkte) | ca. 70 % der RDS-Elemente, aber mit Fehlern | Siemens-Produkte + Generik + Trassen, soweit im Umfang |
| Eignung Bachelorarbeit | als Basis (Stufe 1) | als **Gegenbeispiel**, mit Daten widerlegt | **sehr gut**: messbar, nachvollziehbar, zeigt kontrollierten KI-Einsatz |

**Weg A ist in C enthalten**: Er ist Stufe 1 der Kaskade. C ergänzt A um das, was A nicht kann.

---

## 5. Das gewählte Konzept im Detail

### 5.1 Umfang bestimmen: Welche Bauteile gehören zu Siemens?

Die Entscheidung triffst **du**. Die Diagnose liefert dafür die Kriterien (Datei `1_Kategorien.csv`):

| Kriterium | Spalte in `1_Kategorien.csv` | Bedeutung |
|---|---|---|
| U1 Siemens-typisch | „Hersteller Siemens / SI_-Familie / Siemens-Code“ | Anteil der Bauteile mit Hersteller Siemens, `SI_`-Familie oder Siemens-typischer Produktbezeichnung **[Annahme: Erkennungsmuster]** |
| U2 GA-typische Funktion | „RDS-Funktion GA-typisch“ | Anteil mit RDS-Kennbuchstaben B, K, M, P, Q, S (messen, regeln, antreiben, anzeigen, stellen, bedienen) **[Annahme]** |
| U3 Im LV vorhanden | „Modell im LV“ | Anteil, dessen Modell als Leistungsnummer im SAP-LV steht. **Das stärkste Kriterium**, denn das LV ist verbindlich. |
| U4 Kostengruppe | „KG im Familien-/Typnamen“ und „Kostengruppen-Parameter“ | z. B. `ZWP_480_…` → KG 480 (Gebäudeautomation) **[Annahme]** |
| U5 Planer-Kennzeichen | „ZWP_400_LP8_Abrechnung angehakt“ | nur verwendbar, wenn gepflegt (Regel R6) |

**Vorschlag für eine Regel**, über die du entscheidest:
- Ein Bauteil gehört zum Umfang, wenn es über die Kaskade einer LV-Position zugeordnet werden kann (U3 bzw. Typ-Tabelle).
- Bauteile, die Siemens-typisch sind (U1), aber **nicht** im LV stehen, kommen auf eine eigene Liste „möglicher Nachtrag oder Fehler im LV“.
- Alles andere gehört nicht zum Siemens-Umfang.

### 5.2 Die Kaskade

| Stufe | Prüfung | Vertrauen | Ergebnis |
|---|---|---|---|
| 0 | Hat das Bauteil schon eine eigene LV-Position? | – | behalten (nicht überschreiben), nur gegenprüfen |
| 0b | Ist das Bauteil verschachtelt (Unterfamilie) oder entfallen (Kapitel 6.3)? | – | **nicht zählen** |
| 1 | „Modell“ (normalisiert: Großschreibung, ohne Leerzeichen, erstes Wort) = SAP-`Leistungsnummer`, `L-Identifizierer` oder `Materialnummer` | HOCH | Produkt bestimmt |
| 2 | Typname bzw. Familienname enthält eine Leistungsnummer aus dem LV (z. B. `…_Kanaltemperaturfühler_QAM2112` → `QAM2112…`) | HOCH | Produkt bestimmt |
| 3 | **Typ-Tabelle** (einmal gepflegt): Familie \| Typ → Leistungsnummer, Mengenart, Mengenfaktor | HOCH, wenn geprüft | Produkt bestimmt |
| 4 | Vorschlag aus unscharfem Textvergleich oder KI, **noch nicht geprüft** | NIEDRIG | **Prüfliste**, nicht schreiben |
| 5 | Produkt in genau **einer** LV-Position | – | Position steht fest |
| 6 | Produkt in **mehreren** Positionen → **Abschnitts-Tabelle** (einmal gepflegt): Leistungsnummer \| Anlage → LV-Position | HOCH, wenn geprüft | Position steht fest |
| 7 | sonst | – | Prüfliste „mehrdeutig“ bzw. Fehlerliste |

**Plausibilitätsprüfung mit RDS:**
- Treffen zwei Stufen unterschiedliche Aussagen (z. B. Modell → Fühler, aber RDS-Funktion → Antrieb), wird **nicht** geschrieben.
- Die Kombination kommt dann auf die Prüfliste „Widerspruch“.

### 5.3 „Pflege nur einmal“: die drei Tabellen

| Tabelle | Inhalt | Wer pflegt | Wie oft |
|---|---|---|---|
| **T1 SAP-LV** | Export aus SAP, **unverändert** | niemand, wird nur exportiert | je LV-Stand |
| **T2 Typ-Tabelle** | Familie \| Typ → Leistungsnummer, Mengenart (Stück/Länge), Mengenfaktor (1 = zählt, 0 = Zubehör/Nebenteil) | Fachperson; KI schlägt einmalig vor | **einmal je Typ**. Für Siemens-Familien **[Annahme]** firmenweit wiederverwendbar, weil die Bibliothek projektübergreifend gleich ist |
| **T3 Abschnitts-Tabelle** | Leistungsnummer \| Anlage (RDS-System + Anlagennummer, z. B. `TKA.03`) → LV-Position | Fachperson | **einmal je Kombination**, nur für mehrdeutige Produkte |

Wichtig:
- **Keine Pflege am einzelnen Bauteil.** Das Skript schreibt das Ergebnis in die Bauteile. Ein Mensch entscheidet nur in T2 und T3.
- Beim nächsten Modellstand oder Nachtrag werden alle früheren Entscheidungen automatisch wieder angewendet. Neu entscheiden muss man nur für **neue** Kombinationen.
- **Umfang [Annahme]:** In Diagnose 1 gibt es 148 verschiedene Anlagen (System + Nummer). Wie viele T3-Entscheidungen wirklich nötig sind, zeigt die neue Diagnose in `5a_LV_Positionen.csv` (Bewertung „Position mehrdeutig“) zusammen mit `2_Kombinationen.csv`.

### 5.4 Zielparameter

Es gilt: **eigene Parameter, am Exemplar, nie in `ZWP_…` schreiben.**

| Parameter (Vorschlag) | Ebene | Inhalt |
|---|---|---|
| `LV_Positionsnummer` | Exemplar, Text | LV-Position. Der Name steht bereits in `shared_parameters/` und wird **einheitlich für Modul 1 und 2** verwendet. |
| `LV_Leistungsnummer` | Exemplar, Text | Produkt bzw. Leistung aus SAP; hilfreich, solange die Position noch offen ist |
| `LV_Zuordnung_Status` | Exemplar, Text | `automatisch`, `geprüft`, `offen`, `Widerspruch`, `nicht im Umfang` |

**Warum am Exemplar statt am Typ?** Die Position hängt von der Anlage ab (W5). Zwei gleiche Fühler in zwei Anlagen können zu zwei Positionen gehören. Ein Typparameter, wie heute `LV_Nummer`, kann das nicht abbilden.

### 5.5 Unsicherheit abbilden

- **Vertrauen** ergibt sich aus der Stufe (Tabelle 5.2), **nicht** aus der Selbsteinschätzung einer KI.
- **Prüfliste** (CSV, eine Zeile je Kombination) mit:
  - Vorschlag
  - Alternativen
  - Grund (`niedrig`, `mehrdeutig`, `Widerspruch`)
  - einer leeren Spalte `Entscheidung`
- **Mensch bestätigt:** Bestätigte Zeilen wandern automatisch in T2 oder T3. Damit sind sie für alle weiteren Läufe erledigt.

---

## 6. Nachtrag-Auswertung (Modul 2)

### 6.1 Zwei Vergleiche, beide nötig

| Vergleich | Frage | Ergebnis |
|---|---|---|
| **Modellstand alt ↔ neu** | Was hat sich durch *diese* Planungsänderung geändert? | Nachtragsliste: Mehrung, Minderung, Neu je LV-Position |
| **Soll (LV) ↔ Ist (Modell)** | Passt der aktuelle Modellstand insgesamt zum beauftragten LV? | Plausibilitätsprüfung; deckt auch Fehler im ersten Modellstand oder im LV auf |

**Empfehlung:**
- Die Nachtragsliste kommt aus dem **Versionsvergleich**.
- Soll/Ist ist die **Gegenprobe**. Weicht eine Position im Soll/Ist stark ab, ohne dass der Versionsvergleich eine Änderung zeigt, ist entweder die Zuordnung falsch oder das LV hatte schon vorher eine Abweichung.
- Die neue Diagnose zeigt Soll/Ist schon grob je Leistungsnummer (`5c_Mengen_je_Leistungsnummer.csv`).

### 6.2 Bauteile wiedererkennen

- Über die **UniqueId**. Das macht Modul 2 heute schon.
- Die kurze Element-ID (`IntegerValue`) dient nur zur Anzeige. In Revit 2026 ist `IntegerValue` entfallen. Modul 2 muss deshalb wie `lv_mapping` den sicheren Weg (`Value`, sonst `IntegerValue`) nutzen.

### 6.3 „Entfallen“ ohne Abhängigkeit von der Ansicht

Der Vergleich darf **nie** fragen, ob ein Bauteil sichtbar ist, sondern nur nach einem **Parameterwert**. Ein Bauteil gilt als entfallen, wenn mindestens eins davon zutrifft:

1. Es ist im neuen Modellstand nicht mehr vorhanden (gelöscht).
2. Es ist **verschachtelt** (Unterfamilie). Solche Bauteile werden nie gezählt.
3. Der Parameter, nach dem die Ausblend-Filter des Planers arbeiten, hat den Wert „entfallen“. Den Parameter selbst finden wir mit der neuen Diagnose (siehe unten).
4. Die Revit-Phase „Abgebrochen“ ist gesetzt (die Diagnose zählt das mit).

**So findest du heraus, nach welchem Parameter die Filter arbeiten:**
- Die neue Diagnose schreibt `7_Filter.csv`.
- Darin steht für jeden Ansichtsfilter: Name, Kategorien, **Regeln** (Parameter, Vergleich, Wert) und in wie vielen Ansichten bzw. Vorlagen er etwas **ausblendet**.
- Der Filter, der in den GA-Ansichten ausblendet, verrät den Parameter.
- Wir lesen ihn nur. Ist es ein `ZWP_…`-Parameter, ist das in Ordnung, denn Lesen ist erlaubt.

### 6.4 Mengen in LV-Einheiten je LV-Position

```
Menge(Position) = Summe über alle Bauteile der Position:
                  Mengenfaktor (aus T2) × Grundmenge
Grundmenge      = 1 bei Einheit ST, Länge bei m, Fläche bei m² …
nicht gezählt   = verschachtelte, entfallene, nicht im Umfang
```

- **n:1 und Masterpositionen:**
  - Bauteile werden der Position zugeordnet, die die Menge trägt; bei M/U ist das die **Unterposition**.
  - Die Masterposition wird im Bericht als Summe gezeigt.
  - Weil auch Teile einer Masterposition in den Nachtrag gehen können (W9), wird **je Unterposition** bewertet.
- **Sets** (z. B. Wetterstation aus mehreren Bauteilen): Leitbauteil Mengenfaktor 1, Nebenbauteile 0. Das steht in T2 und wird einmal gepflegt.

### 6.5 Klassifikation je LV-Position

| Fall | Regel |
|---|---|
| NEU_POSITION | Menge alt = 0, Menge neu > 0 |
| MEHRUNG / MINDERUNG | Menge neu > bzw. < Menge alt |
| UNVERÄNDERT | gleich |
| **PRODUKT NICHT IM LV** | Siemens-typisches Bauteil, Leistungsnummer fehlt im LV → Kandidat für eine **neue** LV-Position |

Zu jeder Position gibt es eine Liste der verursachenden Bauteile: neu, entfallen, umgeordnet.

### 6.6 Verknüpfte Modelle (20 Links)

| | Bauteile im offenen Modell | Bauteile in einem Link |
|---|---|---|
| Lesen (Diagnose, Vergleich) | ja | ja, wenn der Link geladen ist |
| Schreiben (Zuweisung) | ja, wenn nicht belegt | **nein**: Ein Link kann aus dem offenen Modell heraus nicht geändert werden |

- In Diagnose 1 lagen 10.882 Elemente der untersuchten Kategorien **im offenen Modell**, darunter alle Siemens-Familien.
- Ob zusätzlich GA-Bauteile in Links liegen, zeigt `6_Verknuepfungen.csv`.
- **Falls ja:** Für diese Bauteile wird die Zuordnung **nicht** in einen Parameter geschrieben, sondern in eine externe Tabelle (Link-Datei + UniqueId → LV-Position). Modul 2 liest beides.

### 6.7 Worksharing: Darf ich schreiben?

- Ein Bauteil, das ein anderer Benutzer gerade belegt, kann nicht geändert werden. Das Schreiben schlägt dann fehl.
- Die Diagnose zählt solche Bauteile („von anderen Benutzern belegt“) und zeigt die Arbeitssätze je Kategorie.
- `lv_mapping` muss solche Fälle künftig **abfangen und melden**, statt abzubrechen.
- **[Offen]** Organisatorisch: Darf Siemens im Planermodell überhaupt eigene Parameter schreiben? Oder arbeitet Siemens in einem eigenen Modell, in dem das Planermodell nur verknüpft ist? Im zweiten Fall gilt Kapitel 6.6, Spalte „Link“: Dann ist die externe Tabelle der Normalfall.

### 6.8 Was sich ändern muss

**An `lv_mapping/`** (später, nicht jetzt):

| Heute | Künftig |
|---|---|
| handgepflegte `LV_Datenbank.csv` | SAP-LV (XLSX) direkt + T2 + T3 |
| Typparameter `LV_Nummer` | Exemplarparameter `LV_Positionsnummer`, `LV_Leistungsnummer`, `LV_Zuordnung_Status` |
| nur exakter Modell-Vergleich | Kaskade 5.2 inkl. Normalisierung (erstes Wort, ohne Leerzeichen) |
| Fehlerliste je Bauteil | Fehler- und Prüfliste **je Kombination** |
| bricht bei belegten Bauteilen ab | meldet „belegt von …“, schreibt den Rest |
| zählt Unterfamilien mit | überspringt verschachtelte Bauteile |
| – | Testwerte `…test` aus Diagnose 1 vorher entfernen |

**An Modul 2 (`dynamo/python/`):**
- Parametername `LV_Positionsnummer` einheitlich. Lesen erst am Exemplar, dann am Typ.
- `IntegerValue` durch den sicheren Weg ersetzen.
- „Entfallen“ nach Kapitel 6.3 bestimmen, nie nach Sichtbarkeit.
- Menge nach Kapitel 6.4 (Mengenfaktor, Einheit, verschachtelte ausschließen).
- Bewertung je **Unterposition**, Master als Summe.
- Soll/Ist-Gegenprobe gegen das SAP-LV.
- Externe Zuordnungstabelle für Link-Bauteile.

---

## 7. KI-Einsatz

| Kriterium | **a) einmaliger Vorschlag, Mensch prüft, Dynamo nutzt nur die Tabelle** | **b) API-Aufruf zur Laufzeit im Python-Knoten** | **c) lokal ohne Cloud** (Textvergleich mit Python-Bordmitteln) |
|---|---|---|---|
| Zuverlässigkeit | hoch (Mensch gibt frei) | mittel (Fehler landen ungeprüft im Modell) | niedrig bis mittel; für Produktcodes im Typnamen hoch |
| Nachvollziehbarkeit | hoch: Begründung + Prüfer in T2 | gering | hoch (Regel bzw. Ähnlichkeitswert sichtbar) |
| Reproduzierbarkeit | **hoch**: Ergebnis ist in T2 eingefroren | **gering**: dieselbe Frage kann andere Antworten geben | vollständig |
| Kosten | über die Copilot-Lizenz abgedeckt **[Annahme]**; per API wären es grob 1,50–3 $ je Projekt (Studie, Kap. 4) | je Lauf erneut | keine |
| Internetbedarf | einmal | bei jedem Lauf | keiner |
| Aufwand für einen Laien | gering: CSV in Copilot einfügen, Antwort als CSV speichern, Zeilen prüfen | hoch: API-Schlüssel, Firmenproxy, Fehlersuche | gering |
| Bei Siemens machbar | **ja, über Copilot (W10)** | nur mit eigenem API-Zugang: **[Offen]**, derzeit nicht bekannt | ja |

**Empfehlung: a)**
- Copilot macht einmalig einen Vorschlag für T2.
- Gefragt wird **je Typ-Kombination** (Familie \| Typ \| Modell aus `2_Kombinationen.csv`), nicht je Bauteil.
- Mitgeschickt werden die LV-Kurztexte **ohne Preise**.
- **c)** läuft als Vorsortierung vorher (Stufe 2: Produktcode im Typnamen). Die KI bekommt nur, was übrig bleibt.
- **b)** wird **nicht** empfohlen.
- **Faustregel [Annahme]:** Unter etwa 100 offenen Typen ist Handarbeit schneller als eine KI-Schleife mit Prüfung.

---

## 8. LV-Format aus SAP

| Format | Einlesen | Fehleranfälligkeit | Empfehlung |
|---|---|---|---|
| **XLSX** | zuverlässig, Ordnungszahlen bleiben Text; lesbar ohne Zusatzinstallation (nachgewiesen am Beispielexport) | gering | **empfohlen**, unverändert lassen, nicht in Excel neu speichern |
| CSV | möglich | mittel: Trennzeichen, Kodierung; Excel macht aus `01.10` → `1,1` | nur, wenn XLSX nicht geht |
| PDF | nur mit Zusatzprogrammen, Spalten müssen erraten werden | hoch | nicht verwenden |

**Nötige Spalten** (Namen wie im SAP-Export):

| Spalte | Wofür |
|---|---|
| `ext. Leistungsnummer` | LV-Position |
| `Objekttyp`, `Unterpositionsnummer` | Master/Unterposition |
| `Leistungsnummer`, `L-Identifizierer`, `Materialnummer` | Abgleich mit „Modell“ |
| `Kurztextzeile 1`, `Kurztextzeile 2` | Prüfliste und KI-Vorschlag. Ein Langtext ist nicht verfügbar (W6). Der Kurztext ist für einen automatischen Abgleich zu unscharf: Am Beispiel liegen `TXM1.8U` und `TXM1.8U-ML` bei 0,58 zu 0,49. |
| `Menge`, `Basismengeneinheit` | Soll/Ist und Mengen je Position |
| `Einheitspreis` | nur für die Nachtragsbewertung; nie an die KI senden |
| `interne Zeile`, `Alternativzeile`, `Eventualzeile` | Zeilen richtig behandeln |

**Alternative „LV mit RDS“:** Gäbe es eine RDS-Spalte im LV, könnte Stufe 6 (Abschnitts-Tabelle) automatisch aus dem LV entstehen. Das gibt es heute nicht (W6). Es bleibt eine **Prozessempfehlung für die Arbeit**: RDS schon bei der LV-Erstellung mitführen.

---

## 9. Entscheidungsregeln

Alle Schwellen sind **[Annahmen]** und sollten nach dem nächsten Diagnoselauf geprüft werden.

| Regel | Bedingung (aus der Diagnose) | Folge |
|---|---|---|
| **R1** Weg A reicht für eine Elementgruppe | „Modell gefüllt“ ≥ 95 % **und** „Modell im LV“ ≥ 90 % (Datei `1_Kategorien.csv`, je Kategorie bzw. Familiengruppe) | nur Stufen 1–2, keine T2 nötig |
| **R2** T2 nötig | „Modell gefüllt“ < 95 % bei Bauteilen im Umfang | Typ-Tabelle anlegen |
| **R3** KI-Vorschlag lohnt | > 100 offene Typ-Kombinationen nach Stufe 1–2 | Variante a) nutzen; darunter von Hand |
| **R4** RDS als Schlüssel zulässig | in `2_Kombinationen.csv` gehört jeder RDS-Schlüssel (System \| Funktion) bei ≥ 95 % der Elemente zu genau einem Produkt | Diagnose 1: **70 % → nicht erfüllt**, RDS nur zur Plausibilitätsprüfung |
| **R5** T3 nötig | `5a_LV_Positionen.csv` enthält „Position mehrdeutig“ | Abschnitts-Entscheidungen einmalig sammeln |
| **R6** `ZWP_400_LP8_Abrechnung` als Umfangsfilter geeignet | angehakt bei ≥ 90 % der Bauteile, die über das LV im Umfang sind, **und** bei ≤ 5 % der Bauteile außerhalb (Spalten „Siemens-typisch UND/OHNE LP8“, „LP8 OHNE Siemens-typisch“) | Diagnose 1: **0 % angehakt → derzeit ungeeignet**; höchstens später als zusätzlicher Hinweis |
| **R7** Link-Weg nötig | `6_Verknuepfungen.csv` zeigt Siemens-typische Bauteile in Links | externe Zuordnungstabelle (6.6) |
| **R8** Kategorie in den Umfang aufnehmen | U3 > 0 oder U1 ≥ 20 % oder U2 ≥ 50 % (Kapitel 5.1) | Kandidat; **du entscheidest** |

---

## 10. Stufenplan

| Stufe | Inhalt | Ergebnis |
|---|---|---|
| **0 Messen** (jetzt) | `GA_Diagnose.dyn` mit deinen 8 Kandidat-Kategorien, der Datenbank-CSV und **dem SAP-LV dieses Projekts** | Umfang festlegen (R8), R1–R7 auswerten, Filterparameter finden, Links und Worksharing klären |
| **1 Minimalversion** | Kaskade Stufen 0–2 und 5; Schreiben in eigene Exemplarparameter; Prüf-/Fehlerliste je Kombination; belegte Bauteile melden | erste Trefferquote |
| **2 Tabellen** | T2 (Typ-Tabelle) und T3 (Abschnitts-Tabelle) mit Prüfliste → Übernahme | volle Abdeckung, Pflege nur einmal |
| **3 KI** | Variante a) über Copilot für die offenen T2-Zeilen (nur, wenn R3 zutrifft) | weniger Handarbeit, messbar |
| **4 Modul 2** | Versionsvergleich + Soll/Ist, Entfallen nach Parameter, Mengen nach 6.4, Links und Worksharing | Nachtragsliste je Unterposition |

---

## 11. Kennzahlen für die Bachelorarbeit

**Zu deinem Einwand bei Frage 10 (Skalierbarkeit):**
- Die Prüfung von Hand ist **keine** Daueraufgabe. Sie findet **einmal für die Arbeit** statt, als Stichprobe, um die Güte zu messen.
- Gezogen wird eine Zufallsstichprobe von **50 Kombinationen**, nicht 500 Bauteilen. 50 Kombinationen können je nach Modell tausende Bauteile abdecken.
- Im laufenden Betrieb messen sich K1 und K4–K10 automatisch. Nur K2 und K3 brauchen die Stichprobe.

| Nr. | Kennzahl | Formel | Quelle |
|---|---|---|---|
| K1 | **Trefferquote (Abdeckung)** | automatisch zugeordnete Bauteile im Umfang ÷ alle Bauteile im Umfang | Skriptbericht |
| K2 | **Präzision** | richtige automatische Zuordnungen ÷ geprüfte automatische (Stichprobe) | Stichprobe |
| K3 | **Falschzuordnungsquote** | 1 − K2 | Stichprobe |
| K4 | **Prüfquote** | Kombinationen auf der Prüfliste ÷ alle Kombinationen (auch je Bauteil) | Skriptbericht |
| K5 | **Mehrdeutigkeitsquote** | Bauteile mit „Position mehrdeutig“ ÷ Bauteile im Umfang | Diagnose 5a |
| K6 | **Widerspruchsquote** | Widerspruch Modell ↔ RDS ÷ Bauteile mit beiden Merkmalen | Skriptbericht |
| K7 | **Pflegeaufwand** | Anzahl einmaliger Entscheidungen (T2- + T3-Zeilen) ÷ Bauteile im Umfang | Tabellen |
| K8 | **Soll/Ist-Abweichung** | je Position \|Modellmenge − LV-Menge\| ÷ LV-Menge | Diagnose 5c / Modul 2 |
| K9 | **Wiederverwendung** | Anteil Kombinationen eines neuen Modellstands, die schon entschieden sind | Skriptbericht |
| K10 | **Datenqualität** | Anteil Modell gefüllt, RDS gefüllt, verschachtelte Bauteile, doppelte RDS-Codes | Diagnose |

K7 und K9 belegen deine Kernforderung **„Pflege nur einmal“** mit Zahlen.

---

## 12. Offene Fragen

| Nr. | Frage | Stand |
|---|---|---|
| F1 | Nach welchem Parameter arbeiten eure Ausblend-Filter? | **wird durch die neue Diagnose beantwortet** (`7_Filter.csv`). Danach bitte bestätigen. |
| F2 | Arbeitet Siemens in LP 8 im Planermodell oder in einem eigenen Modell mit Links? | offen; wichtig für 6.6 und 6.7 |
| F3 | Gibt es einen Kostengruppen-Parameter? | Diagnose 1 hat nur die bekannten Namen geprüft. Die neue Diagnose durchsucht **alle** Parameter (`3_Parameter.csv`, Spalte „möglicher Kostengruppen-Parameter“). Hinweis: Die KG steht bei Generikfamilien im Namen (`ZWP_480_…`). |
| F4 | Wer pflegt `ZWP_400_LP8_Abrechnung`, und wie verlässlich? | Diagnose 1: nirgends gesetzt. Wer es pflegen soll, kann nur der Planer bzw. die Projektleitung beantworten. |
| F5 | Gehört zu einem RDS-Schlüssel immer genau eine LV-Position? | **beantwortet: Nein** (Kapitel 3, mit Daten belegt) |
| F6 | Darf Siemens im Planermodell eigene Parameter anlegen und beschreiben, und auf welchem Arbeitssatz? | offen |
| F7 | Gehören Kabeltrassen der KG 480 (`ZWP_480_Kabelrinne`, `…Kabelleiter`) zum Siemens-LV? Wenn ja: Abrechnung in Metern, Formteile im Meterpreis? | offen (aus Diagnose-Auswertung 1) |
| F8 | Gibt es eine Copilot-Variante mit API-Zugang (für Variante b)? | nur relevant, falls b) später gewünscht |
| F9 | Kannst du den SAP-LV-Export **dieses Projekts** für den Diagnoselauf verwenden? | Er bleibt auf deinem Rechner; ins öffentliche Repository kommt er nicht. |
