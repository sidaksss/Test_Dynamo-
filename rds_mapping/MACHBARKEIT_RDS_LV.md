# Machbarkeitsstudie: LV-Zuordnung über RDS-Kennzeichen, Modell und KI

> **Status:** Studie, keine Umsetzung. Die Prototypen in `prototypen/` lesen nur Daten. Getestet sind sie lediglich mit simulierten Revit-Daten (Mock) und mit dem SAP-Beispielexport. **Ein Test in echtem Revit steht noch aus.**
> **Stand:** Oktober 2026.
> **Grundlage:**
> - `PROJEKT_ZUSAMMENFASSUNG.md`
> - ein Screenshot der Eigenschaftenpalette (Bauteil `WK_238`)
> - ein SAP-LV-Export als Formatbeispiel (anderes Projekt, 135 Zeilen, 48 Spalten)
>
> **Kennzeichnung im Text:**
> - **[Befund]**: am Beispielmaterial nachgeprüft.
> - **[Annahme]**: plausibel, aber nicht belegt.
> - **[Offen]**: braucht eine Antwort von dir (Kapitel 10).

---

## 0. Ergebnis auf einen Blick

1. **Die wichtigste Brücke ist nicht das RDS, sondern die SAP-Spalte `Leistungsnummer`. [Befund]**
   - Bei Siemens-Produkten steht dort die Produktbezeichnung, z. B. `TXM1.16D` oder `PXC7.E400L`.
   - Das ist genau der Wert, der in Revit im Typparameter „Modell“ stehen sollte.
   - Das SAP-LV kann damit **selbst die Datenbank sein**. Die handgepflegte `LV_Datenbank.csv` wird überflüssig.
2. **Ein Produkt gehört fast nie zu genau einer LV-Position. [Befund]**
   - Im Beispiel-LV kommt **jedes der 9 Produkte in 6–7 Positionen vor**: einmal pro LV-Abschnitt, also vermutlich pro Gebäude bzw. Schaltschrank.
   - Daraus folgt: Die LV-Position hängt vom **Produkt** (Typebene) **und vom Ort/System** (Exemplarebene) ab.
3. **Folge für Revit:**
   - Die LV-Position gehört an das **Exemplar**, nicht an den Typ.
   - Das löst gleichzeitig den Widerspruch zwischen Modul 1 und Modul 2 (Abschnitt 5 der Projektzusammenfassung).
4. **Das RDS-Kennzeichen eignet sich für zwei Dinge:**
   - Den **Ort/System-Teil** (Exemplar), um den richtigen LV-Abschnitt zu wählen.
   - Den **Funktions-Teil** als Ersatzschlüssel, wenn „Modell“ fehlt.
   - Es beschreibt aber die *Funktion* („Temperaturfühler am Nacherhitzer“) und nicht das *Produkt*.
   - **Ein RDS-Schlüssel führt deshalb nicht immer zu genau einer LV-Position** (Kapitel 1.4).
5. **Das SAP-LV enthält keine RDS-Bezüge. [Befund]**
   - Ein reiner Textabgleich (Kurztext) ist unsicher: Varianten wie `TXM1.8U` und `TXM1.8U-ML` liegen beim Textvergleich nah beieinander.
6. **Empfehlung:**
   - Eine **regelbasierte Zuordnungskaskade**.
   - Die KI nur **einmalig und offline** als Vorschlagsgeber für die Übersetzungstabelle, mit menschlicher Freigabe (Variante a).
   - **Keine KI zur Laufzeit** in Dynamo.
   - Beginnen mit dem Diagnose-Skript (Stufe 0), um echte Zahlen zu bekommen.

---

## 1. Übersetzungstabelle RDS → LV

### 1.1 Begriffe kurz erklärt

- **RDS (Reference Designation System):** Kennzeichnungssystem nach DIN EN IEC 81346. Ein Kennzeichen besteht aus *Aspekten*, die durch ein Vorzeichen eingeleitet werden:
  - `+` Ort (wo?)
  - `=` Funktion (wozu?)
  - `-` Produkt (was?)
  - `#` sonstiger Aspekt, hier vermutlich das System bzw. die Anlage
- **LV (Leistungsverzeichnis):** Liste der beauftragten Leistungen. Jede Position hat eine Ordnungszahl (z. B. `04.01.01.20`), einen Kurztext, eine Menge und einen Preis.
- **Schlüssel:** der Wert, mit dem in einer Tabelle nachgeschlagen wird.
- **Typ- und Exemplarebene:**
  - Ein *Typ* ist z. B. „Kanalfühler QAM2112.040“.
  - Ein *Exemplar* ist jeder einzelne eingebaute Fühler im Modell.

### 1.2 Zerlegung des Beispiel-Kennzeichens

`+S2.C1.01.0703.__B1.B1.045#432.TKA.03=BTAZ.003-_._.__`

| Teil | Wert | Einzelparameter | Bedeutung | Ebene |
|---|---|---|---|---|
| `+` Ort | S2 | RDS_Projekt | Projekt | Exemplar (immer gleich) |
| | C1 | RDS_Modul | Modul | Exemplar |
| | 01 | RDS_Teilmodul | Teilmodul | Exemplar |
| | 0703 | RDS_Gebaeude | Gebäude | Exemplar |
| | \_\_B1 | RDS_Geschoss | Geschoss (Platzhalter `__` aufgefüllt) | Exemplar |
| | B1.045 | RDS_Segment | Segment/Bereich | Exemplar |
| `#` System | 432 | RDS_System | **[Annahme]** Kostengruppe DIN 276 (432 = Teilklimaanlagen) | eher Anlage |
| | TKA | RDS_Systemkennzeichnung | Teilklimaanlage | eher Anlage |
| | 03 | RDS_SystemNum | Anlagennummer (3. TKA) | Exemplar |
| `=` Funktion | BTAZ | RDS_Funktion | **[Annahme]** BT = Temperatursensor (Kennbuchstaben nach IEC 81346-2), AZ = Projektzusatz | **typnah** |
| | 003 | RDS_FunktionsNum | Zählnummer | Exemplar |
| `-` Produkt | `_._.__` | – | leer (nur Platzhalter) | – |
| – | 1 | RDS_Bauabschnitt | nicht im Code enthalten | Exemplar |
| – | BB137A | RDS_Raum | nicht im Code enthalten | Exemplar |

**Zum Ort der Parameter:**
- **[Befund, Screenshot]** Die RDS-Parameter erscheinen in der Eigenschaftenpalette zusammen mit „Kennzeichen“ und „Kommentare“. Das sind Exemplarparameter.
- **[Annahme]** Die RDS-Parameter sind also wahrscheinlich ebenfalls **Exemplarparameter**.
- Das ist fachlich auch folgerichtig: Ort und Zählnummer unterscheiden sich von Fühler zu Fühler.
- Das Diagnose-Skript (Kapitel 5) prüft das an echten Daten.

`RDS_Projekt` ist im Screenshot grau dargestellt, also schreibgeschützt. Für die Zuordnung spielt das keine Rolle.

### 1.3 Welcher Teil eignet sich als Schlüssel?

| Kandidat | Beispiel | Bewertung |
|---|---|---|
| ganzes Kennzeichen | `+S2…=BTAZ.003-…` | ungeeignet: für jedes Exemplar anders |
| Funktion ohne Nummer | `BTAZ` | gut als **Gerätegruppe**, aber kein Produkt |
| Systemart + Funktion | `TKA\|BTAZ` | besser: „Temperaturfühler an Teilklimaanlage“ |
| Systemart + Funktion + Familie | `TKA\|BTAZ\|<Familienname>` | am trennschärfsten ohne „Modell“ |
| Ort/System mit Nummer | `0703`, `TKA.03` | **nicht** für das Produkt, aber für die **Wahl des LV-Abschnitts** |

**Normalisierung**, also das Vereinheitlichen vor dem Vergleich:
- Großschreibung, Leerzeichen entfernen.
- Die Platzhalter `_` entfernen.
- Zählnummern (`RDS_FunktionsNum`, `RDS_SystemNum`) weglassen.
- Die **Einzelparameter** verwenden, nicht den zusammengesetzten `RDS_Code`. Der Code ist nur über die Position der Punkte zerlegbar, und `RDS_Segment` enthält selbst einen Punkt (`B1.045`). Das ist fehleranfällig.
- Der Code dient dann als Gegenprobe: Das Diagnose-Skript meldet, ob `RDS_Code` zu den Einzelparametern passt.

### 1.4 Gehört zu einem RDS-Schlüssel immer genau eine LV-Position? – Nein.

Es gibt drei Gründe, jeder mit Beleg bzw. Einordnung:

1. **Funktion ≠ Produkt. [Annahme, fachlich begründet]**
   - `BTAZ` (Temperaturfühler) kann je nach Einbausituation ein Kanal-, Tauch- oder Anlegefühler sein.
   - Im LV sind das verschiedene Positionen mit verschiedenen Preisen.
2. **Gleiches Produkt, mehrere LV-Abschnitte. [Befund]**
   - Im Beispiel-LV steht `TXM1.16D` in den Positionen 01.20, 04.01.01.20, 04.02.01.20 … 04.06.01.20, also 7 Positionen.
   - Das gilt für alle 9 Produkte.
   - Welche Position gilt, entscheidet der Ort bzw. die Anlage, also der Exemplar-Teil des RDS.
3. **Mehrere Bauteile, eine Position (n:1). [Befund]**
   - Es gibt Masterpositionen (Objekttyp `M`) mit Unterpositionen (`U`).
   - Dazu kommen Sammelpositionen wie die von dir genannte Wetterstation.

Die richtige Aussage für die Arbeit lautet deshalb:

> **Produktschlüssel (Typebene) + Ortsschlüssel (Exemplarebene) → genau eine LV-Position**, sofern das LV nach Orten/Anlagen gegliedert ist und die Gliederung bekannt ist.
>
> Ein RDS-Funktionsschlüssel allein liefert meist nur eine *Kandidatenmenge*.

### 1.5 Ist eine Tabelle „RDS-Schlüssel → LV-Nummer“ sinnvoll?

Nicht in dieser Form. Besser sind **zwei kleine Tabellen** statt einer großen:

| Tabelle | Inhalt | Größe [Annahme] | Pflege |
|---|---|---|---|
| **A: Produkt-Übersetzung** | Schlüssel (`TKA\|BTAZ` oder Familie/Typ) → `Leistungsnummer` | so viele Zeilen wie verschiedene Gerätegruppen, ca. 30–150 | einmal pro Projekt, mit KI-Vorschlag (Kap. 4) |
| **B: Abschnitts-Zuordnung** | Ortsschlüssel (z. B. `0703` oder `TKA.03`) → LV-Abschnitt (z. B. `04.01`) | so viele Zeilen wie Gebäude/Anlagen, ca. 5–30 | von Hand, wenige Minuten |

Die LV-Position ergibt sich dann **automatisch** aus dem SAP-Export: In Abschnitt `04.01` wird die Zeile mit `Leistungsnummer = TXM1.16D` gesucht, Ergebnis `04.01.01.20`.

**Erzeugung mit wenig Handarbeit:**
1. Das Diagnose-Skript sammelt alle vorkommenden Kombinationen aus Funktion, System, Familie, Typ und Modell. Doppelte werden zusammengefasst.
2. Für Typen *mit* gepflegtem „Modell“ wird Tabelle A automatisch befüllt: Man sieht, welches Modell zu welchem `TKA|BTAZ` gehört. Die gut gepflegten Typen „lehren“ damit die schlecht gepflegten.
3. Für den Rest macht die KI (offline) einen Vorschlag. Ein Mensch bestätigt ihn (Kap. 4a).
4. Tabelle B legt ein Mensch einmal an, denn die LV-Gliederung kennt nur der Projektverantwortliche.

**[Offen]** Wonach ist das LV gegliedert (Gebäude, Anlage, Schaltschrank, Bauabschnitt)?

---

## 2. Zuordnungskaskade

Eine **Kaskade** ist eine feste Reihenfolge von Prüfungen. Die erste, die zu einem eindeutigen Ergebnis führt, gewinnt. Jede Stufe vergibt ein **Vertrauensniveau**.

```
Für jedes Exemplar:
 0. LV-Position am Exemplar schon vorhanden?        → behalten, nur gegenprüfen
 ── Schritt A: Produkt bestimmen (Ergebnis: Leistungsnummer) ──
 1. Modell exakt = Leistungsnummer/L-Identifizierer im SAP-LV     Vertrauen HOCH
 2. Produktcode aus Familien-/Typname extrahiert = Leistungsnummer Vertrauen HOCH
 3. Tabelle A (freigegeben): RDS-Funktion+System(+Familie)       Vertrauen MITTEL–HOCH
 4. Unscharfer Textvergleich (Kommentare/Typname ↔ Kurztext)       Vertrauen NIEDRIG → nur Prüfliste
 ── Schritt B: Position wählen ──
 5. Alle LV-Positionen mit dieser Leistungsnummer suchen
    - genau eine            → fertig
    - mehrere               → Tabelle B (Ortsschlüssel → Abschnitt) anwenden
    - danach noch mehrere   → Prüfliste „mehrdeutig“
    - keine                 → Fehlerliste „Produkt nicht im LV“ (möglicher Nachtrag!)
 6. Nichts gefunden        → Fehlerliste
```

**Stufe 2 erklärt:**
- Familien- und Typnamen enthalten oft die Produktbezeichnung, z. B. `Siemens_QAM2112_Kanalfuehler`.
- Ein Suchmuster (regulärer Ausdruck) prüft, ob eine der Leistungsnummern aus dem LV im Namen vorkommt.
- Das ist exakt, nachvollziehbar und braucht keine KI.

**Widersprüche** (Stufe 1 sagt `QAM2112.040`, Tabelle A sagt `QAE2112.010`):
- **Nicht schreiben.** Das Exemplar kommt auf die Prüfliste mit Grund „Widerspruch Modell ↔ RDS“ und beiden Kandidaten.
- Kein Merkmal „gewinnt“ automatisch. Ein Widerspruch deutet fast immer auf einen Pflegefehler im Modell hin, und den soll ein Mensch sehen.
- Die Widerspruchsquote ist selbst eine gute Kennzahl für die Datenqualität (Kap. 7.3).

**Mehrdeutige Treffer** (mehrere Kandidaten mit gleichem Vertrauen):
- Nie automatisch den „ersten“ nehmen.
- Prüfliste mit allen Kandidaten, Kurztext und Abschnitt ausgeben. Der Mensch wählt.
- Die Wahl wird in Tabelle A oder B gespeichert, damit sie beim nächsten Lauf automatisch gilt.

---

## 3. LV-Quelle aus SAP

### 3.1 Was der Beispielexport tatsächlich enthält [Befund]

Ausgewertet mit `prototypen/sap_lv_lesen.py`:

| Erwartung (aus deiner Beschreibung) | Tatsächliche Spalte im Export | Bemerkung |
|---|---|---|
| LV-Positionsnummer | `ext. Leistungsnummer` | Ordnungszahl, z. B. `04.01.01.20`; als **Text** gespeichert (gut) |
| Leistungsnummer | `Leistungsnummer` | bei Produkten = Produktbezeichnung (`TXM1.16D`); bei Pauschalen Codes wie `FP_Z499`, `DL_Z501` |
| – | `L-Identifizierer`, `Materialnummer` | Produkttyp bzw. Bestellnummer; können abweichen (`PXC7.E400L` → `S55375-C105`) |
| Menge, Basismengeneinheit | `Menge`, `Basismengeneinheit` | im Beispiel nur `ST` (Stück) |
| Kurztext | `Kurztextzeile 1` + `Kurztextzeile 2` | zweizeilig, kurz |
| **Langtext** | **fehlt** | **[Offen]** Lässt sich der Langtext mit exportieren? |
| Einheitspreis, Gesamtpreis | `Einheitspreis`, `Su Einheitspreis` | Gesamtpreis = Menge × EP (nachgerechnet: 4 × 195,00 = 780,00) |
| – | `Objekttyp` (M/U), `Unterpositionsnummer` | Master- und Unterpositionen |
| – | `interne Zeile` (I) | interne Zeilen, vermutlich nicht für den Kunden |
| RDS-Bezug | **keiner** | keine Spalte, kein Text mit RDS-Muster |

**Zeilenarten im Beispiel:**
- 78 normale Positionen
- 14 Master- und 35 Unterpositionen
- 8 Titel- bzw. Hinweiszeilen

**Vertrauliche Inhalte:**
- Rund 25 der 48 Spalten sind interne Kalkulationsdaten (Einkaufspreis, Rabatte, Spannen).
- Ein Kurztext enthält einen Personennamen.
- Für die Zuordnung braucht man diese Spalten nicht. Sie sollten vor jeder Weitergabe entfernt werden (Kap. 4).
- Ins (öffentliche) Repository wurde deshalb nur eine **anonymisierte, teils synthetische** Kopie gelegt: `beispieldaten/SAP_LV_Export_Beispiel_anonymisiert.xlsx`.

### 3.2 Formatvergleich

| Kriterium | XLSX | CSV | PDF |
|---|---|---|---|
| Zuverlässigkeit beim Einlesen | **hoch**: Zellen und Spalten sind eindeutig | mittel: Trennzeichen, Dezimalkomma, Kodierung und Zeilenumbrüche im Text müssen stimmen | **niedrig**: Text muss aus dem Seitenlayout erraten werden (Spalten, Seitenumbrüche, mehrzeilige Texte) |
| Bleibt `01.10` Text? | ja (im Export als Text gespeichert) | nur, wenn niemand die Datei in Excel öffnet und neu speichert (sonst `1,1`) | ja, aber muss erst erkannt werden |
| Lesbar in Dynamo ohne Zusatzinstallation | **ja**: mit Python-Bordmitteln nachgewiesen (`sap_lv_lesen.py` liest den Beispielexport vollständig) oder per Dynamo-Knoten `Data.OpenXMLImportExcel` | ja | **nein**: PDF-Bibliotheken müssten nachinstalliert werden |
| Aufwand | gering | gering | hoch |
| Fehleranfälligkeit | gering | mittel | hoch |

**Empfehlung:** **XLSX direkt aus SAP**, unverändert verwenden. Nicht in Excel bearbeiten und neu speichern. PDF nur als Notlösung.

**Notwendige Spalten:**

| Spalte | Wofür |
|---|---|
| `ext. Leistungsnummer` | Ziel: die LV-Position |
| `Leistungsnummer`, `L-Identifizierer`, `Materialnummer` | Abgleich mit „Modell“ (Stufe 1/2) |
| `Kurztextzeile 1`, `Kurztextzeile 2` (+ Langtext, falls möglich) | Prüfliste, Textvergleich, KI-Vorschlag |
| `Objekttyp`, `Unterpositionsnummer`, `interne Zeile`, `Alternativzeile`, `Eventualzeile` | Zeilenart erkennen und richtig behandeln |
| `Menge`, `Basismengeneinheit` | Mengenabgleich Modell ↔ LV (Kennzahl), Modul 2 |
| `Einheitspreis` | optional, nur für Modul 2 (Nachtragsbewertung) |

### 3.3 Zwei Fälle: LV mit oder ohne RDS-Bezug

| | **Fall 1: LV ohne RDS (Beispiel, Normalfall)** | **Fall 2: LV mit RDS-Spalte (Alternative)** |
|---|---|---|
| Brücke Revit → LV | Produkt (Modell ↔ Leistungsnummer) + Abschnittstabelle B | RDS-Schlüssel direkt |
| Rolle des Textabgleichs | nur Ausweichweg, nur Vorschläge | kaum nötig |
| Handarbeit | Tabelle A (teilweise) + Tabelle B | fast keine |
| Risiko | Pflege von „Modell“ bzw. Familiennamen | Tippfehler im RDS beidseitig, Platzhalter `__` |
| Folge für die Arbeit | Kaskade nötig, Kennzahlen messen | Zuordnung fast trivial; dann lohnt es sich, SAP-seitig RDS zu pflegen |

**Hinweis für die Arbeit:** Fall 2 wäre eine **Prozessempfehlung**. Wenn das RDS-Kennzeichen bei der LV-Erstellung schon bekannt ist, sollte SAP es mitführen. Das ist ein starkes Ergebnis für ein Konzept zur systematischen Nachtragserfassung.

---

## 4. Einsatz von KI

### 4.1 Varianten

**a) KI einmalig offline → Vorschlagstabelle → Mensch prüft → Dynamo nutzt nur die fertige Tabelle**
1. Das Diagnose-Skript liefert die *eindeutigen* Kombinationen (Kap. 4.3).
2. Ein Skript außerhalb von Revit schickt jede Kombination zusammen mit der Liste der LV-Kandidaten (Leistungsnummer + Kurztext, **ohne Preise**) an die KI.
3. Die KI antwortet mit Vorschlag, Begründung und Alternativen.
4. Ein Mensch setzt in der Tabelle `bestätigt`, `abgelehnt` oder `korrigiert`.

**b) Python-Knoten in Dynamo ruft zur Laufzeit eine KI-Schnittstelle (API) auf**
- Technisch möglich: CPython3 kann HTTPS-Anfragen mit Bordmitteln senden.

**c) Lokale Verfahren ohne Cloud**, alle mit Python-Bordmitteln möglich:
- c1: Produktcode-Erkennung in Familien-/Typnamen (Suchmuster)
- c2: unscharfer Textvergleich (`difflib`, Wort-Überlappung)
- c3: „Lernen“ aus gut gepflegten Typen: Gleicher RDS-Schlüssel und gleiche Familie bekommen dasselbe Produkt wie ein Typ mit gepflegtem „Modell“.

### 4.2 Bewertung

| Kriterium | a) KI offline + Freigabe | b) KI zur Laufzeit | c) lokal |
|---|---|---|---|
| Zuverlässigkeit | hoch, weil ein Mensch freigibt | mittel; Fehler landen ungeprüft im Modell | c1/c3 hoch, c2 niedrig |
| Nachvollziehbarkeit | hoch: Begründung + Prüfer in der Tabelle | gering | c1/c3 hoch, c2 mittel (Ähnlichkeitswert) |
| Reproduzierbarkeit | **hoch**: Das Ergebnis ist in der Tabelle eingefroren | **gering**: dieselbe Frage kann andere Antworten liefern (siehe unten) | **vollständig**: gleiche Eingabe, gleiches Ergebnis |
| Datenschutz / Firmenvorgaben | gut steuerbar: nur nötige Spalten, einmalig | jeder Lauf sendet Daten; der API-Schlüssel steckt im Skript oder auf dem Rechner | keine Datenweitergabe |
| Kosten | einmalig, gering (siehe unten) | pro Lauf erneut | keine |
| Internetbedarf | nur einmal beim Erzeugen | bei jedem Lauf; Firmenproxy kann blockieren | keiner |
| Aufwand für Laien | mittel: Tabelle prüfen | gering in der Bedienung, hoch bei Fehlersuche | gering |

**Zur Reproduzierbarkeit:**
- Bei aktuellen Claude-Modellen lässt sich die „Temperatur“ (der Zufallsanteil der Antwort) **nicht mehr einstellen**. Die Schnittstelle lehnt den Parameter ab.
- Wiederholbarkeit erreicht man deshalb nur, indem man die Antwort **speichert** (Variante a), nicht durch erneutes Fragen.
- Das ist das stärkste Argument gegen Variante b.

**Grobe Kostenabschätzung.** Das ist eine Größenordnung, keine Zusage.

Listenpreise von Anthropic, Stand Oktober 2026, in US-Dollar pro 1 Mio. Token:

| Modell | Eingabe | Ausgabe |
|---|---|---|
| Claude Haiku 5.5 | 0,10 | 0,50 |
| Claude Sonnet 5.5 | 2 | 10 |
| Claude Opus 5.5 | 4 | 20 |

Die Batch-Schnittstelle kostet die Hälfte, ist aber nicht sofort, sondern zeitversetzt. Ein Token entspricht etwa ¾ Wort.

Annahmen für die Rechnung:
- 500 eindeutige Kombinationen
- LV mit 1.000 Positionen × 30 Token = 30.000 Token Kandidatenliste
- 25 Kombinationen pro Anfrage, also 20 Anfragen

Rechnung:
- Eingabe: 20 × 30.000 Token = 0,6 Mio. Token
- Ausgabe: ca. 0,03 Mio. Token
- Ergebnis: rund 1,50 $ mit Sonnet 5.5 bzw. 3 $ mit Opus 5.5, **einmalig pro Projekt**

**Die Kosten entscheiden also nicht.** Entscheidend sind Zuverlässigkeit und Reproduzierbarkeit.

**[Offen]** Welche KI ist bei Siemens freigegeben, und über welchen Zugang (eigene Firmenplattform oder direkte API)?

### 4.3 KI nur einmal pro eindeutiger Kombination befragen

1. Für jedes Exemplar einen **Kombinationsschlüssel** bilden: `normalisiert(Modell | Familie | Typ | RDS_Funktion | RDS_Systemkennzeichnung)`.
2. Doppelte Schlüssel entfernen. Aus z. B. 5.000 Fühlern werden so vielleicht 60 Kombinationen. **[Annahme]** Wie stark das zusammenschrumpft, misst die Diagnose (`2_Typen.csv`).
3. Ausgewählte Freitexte pro Kombination mitsenden:
   - „Kommentare“ ist exemplarbezogen. Den häufigsten Wert der Kombination mitsenden, nicht alle.
4. Antworten in einer **Cache-Tabelle** speichern, also einer Tabelle mit bereits gestellten Fragen und Antworten:
   - Schlüssel, Vorschlag, Alternativen, Begründung, Vertrauen, Status, Prüfer, Datum
   - Bei jedem weiteren Lauf werden nur **neue** Schlüssel nachgefragt.

**Wie gut eignen sich die Textquellen?**

| Quelle | Eignung | Grund |
|---|---|---|
| Familienname / Typname | **gut** | enthält oft Hersteller, Produktgruppe oder sogar die Produktbezeichnung |
| Kommentare | **schwach** | beschreibt die *Funktion* („Temperatursensor Nacherhitzer“), nicht das Produkt; ist pro Exemplar unterschiedlich |
| RDS_Funktion + System | **mittel** | eindeutige Gerätegruppe, aber nicht das konkrete Produkt |

**[Befund]** Ein Textvergleich von „Temperatursensor Nacherhitzer“ gegen alle Kurztexte des Beispiel-LV findet nichts Sinnvolles: Die beste Ähnlichkeit liegt bei 0,29. Allerdings enthält das Beispiel-LV auch keine Fühler. Mit echten Projektdaten wiederholen.

### 4.4 Unsicherheit abbilden

- **Vertrauen aus der Herkunft, nicht aus der Selbsteinschätzung der KI:**
  - Stufe 1/2 = HOCH
  - freigegebene Tabelle = HOCH
  - KI-Vorschlag, dem ein lokales Verfahren zustimmt = MITTEL
  - nur KI oder nur Textvergleich = NIEDRIG
  - Die Selbsteinschätzung einer KI („90 % sicher“) ist erfahrungsgemäß schlecht kalibriert. Man sollte sich nicht darauf verlassen.
- **Schwellen:** HOCH wird geschrieben, MITTEL und NIEDRIG kommen auf die **Prüfliste** und werden nie automatisch geschrieben.
- **[Befund]** Der Textvergleich am Beispiel-LV zeigt das Risiko:

  | Suchtext | Bester Treffer | Zweiter Treffer |
  |---|---|---|
  | „Universalmodul 8 Kanal“ | `TXM1.8U` mit 0,58 | `TXM1.8U-ML` mit 0,49 (Preisunterschied ca. Faktor 1,7) |
  | „Automationsstation BACnet“ | `PXC7.E400L` mit 0,54 | `FP_Z299` mit 0,54 (Gleichstand) |

  Textvergleich taugt also nur für Vorschläge.
- **Mensch bestätigt:** Die Prüfliste ist eine CSV mit einer Spalte `Entscheidung`. Bestätigte Zeilen wandern in Tabelle A bzw. B.

---

## 5. Revit-Seite

### 5.1 RDS-Parameter zuverlässig lesen

- **Erst am Exemplar suchen, dann am Typ.** Damit funktioniert es, egal wo der Parameter angelegt ist.
- **Gleichnamige Parameter erkennen:** `GetParameters(name)` statt nur `LookupParameter(name)`. Bei mehr als einem Treffer warnen, denn ein Familienparameter und ein gemeinsam genutzter Parameter können denselben Namen haben.
- **Werte als Text lesen und den Datentyp beachten:** Ja/Nein-Parameter liefern 0/1.
- **Für den Schlüssel die Einzelparameter nehmen**, den `RDS_Code` nur zur Gegenprobe (Kap. 1.3).
- **„Modell“, „Kommentare“, „Kennzeichen“ usw. über BuiltInParameter lesen.** Das ist unabhängig von der Sprache der Revit-Oberfläche.

### 5.2 Diagnose-Skript (Prototyp, nur lesen)

Dateien:
- `prototypen/RDS_Diagnose.dyn`
- Code zum Nachlesen: `prototypen/rds_diagnose.py`
- Bedienung: `ANLEITUNG_DIAGNOSE.md`

**Was es tut:**
- Es fragt per Fenster die Kategorien ab und liest für jedes Element:
  - Modell, Hersteller, Typkommentare, Beschreibung, Kommentare, Kennzeichen
  - alle 14 RDS-Parameter
  - `ZWP_400_LV_Position`, `ZWP_400_LP8_Abrechnung`, `ZWP_400_Auswahlfilter`
  - `LV_Nummer`, `LV_Positionsnummer`
  - weitere Namen, die man im Eingabefeld angeben kann
- Es schreibt einen Ordner `RDS_Diagnose_<Datum>` auf den Desktop:

| Datei | Inhalt | Beantwortet |
|---|---|---|
| `1_Elemente.csv` | eine Zeile pro Element: alle Werte, Fundort je Parameter (E/T/E+T/-), zerlegter RDS_Code, Kandidatenschlüssel, Gegenprobe RDS_Code | Rohdaten für alles Weitere |
| `2_Typen.csv` | eine Zeile pro Typ: Anzahl Exemplare, Modell, Anzahl **verschiedener** RDS-Funktionen/-Systeme innerhalb des Typs, vorhandene LV-Werte | Ist der RDS-Schlüssel typbezogen? (1 = ja, >1 = nein) |
| `3_Parameter.csv` | eine Zeile pro Parameter: wie oft am Exemplar/Typ/nicht gefunden, Anteil gefüllt, Datentyp, doppelte Namen | Wo liegen die Parameter, wie gut sind sie gepflegt? |

- Im Knoten „Ergebnis“ erscheinen die Kernzahlen:
  - Typen ohne Modell
  - Elemente mit RDS_Code
  - Typen mit einheitlichem RDS-Schlüssel
  - Fundort von RDS_Code

**Status:** Im Mock wurden folgende Fälle geprüft:
- RDS am Exemplar
- Funktion am Typ
- uneinheitlicher Typ
- Element ohne Typ
- doppelter Parametername
- Ja/Nein-Parameter

**Der Test in echtem Revit steht aus.**

### 5.3 Ist `ZWP_400_LV_Position` als Zielparameter geeignet?

**Dafür:**
- Der Name sagt genau, wofür der Parameter gedacht ist.
- Er existiert bereits im Modell, es muss also kein neuer Parameter angelegt werden.
- Er liegt vermutlich am **Exemplar**. Das ist laut Kapitel 0 genau die richtige Ebene.

**Dagegen bzw. ungeklärt:**
- Gehört er zu einem Firmen-Workflow („ZWP_400“), der ihn selbst befüllt oder auswertet? Dann darf das Skript ihm nicht ungefragt in die Quere kommen.
- Der Datentyp ist unbekannt. Er sollte Text sein, damit `04.01.01.20` nicht verändert wird.
- Was bedeuten `ZWP_400_LP8_Abrechnung` (Ja/Nein, vermutlich Abrechnung in Leistungsphase 8) und `ZWP_400_Auswahlfilter`? Sie könnten für Modul 2 nützlich sein.

**Empfehlung:**
- Geeignet, **sofern** die Diagnose „Exemplar, Text“ zeigt und der ZWP-Prozess es erlaubt. **[Offen]**
- Bis dahin den Zielparameter im Skript **einstellbar** lassen. Das ist schon heute so (Eingabe „Name des LV-Parameters“).

---

## 6. Auswirkungen auf den Bestand

### 6.1 Änderungen an `lv_mapping/`

| Heute | Künftig |
|---|---|
| handgepflegte `LV_Datenbank.csv` (Modell → LV-Nummer) | SAP-XLSX direkt einlesen; dazu Tabelle A (Übersetzung) und Tabelle B (Abschnitte) als kleine CSVs |
| Ziel: **Typ**parameter `LV_Nummer` | Ziel: **Exemplar**parameter (`ZWP_400_LV_Position` oder einheitlicher Name, s. 6.2) |
| eine Stufe: Modell exakt | Kaskade aus Kapitel 2 |
| Fehlerliste | Fehlerliste **+ Prüfliste** (mehrdeutig, Widerspruch, niedriges Vertrauen) mit Spalte `Entscheidung` |
| „nicht überschreiben“ | bleibt; zusätzlich Bericht „vorhandener Wert weicht vom Vorschlag ab“ |

Unverändert übernehmen lassen sich:
- die Kategorieauswahl
- die Transaktion
- die CSV-Ausgabe
- der Python-Stil

Das bestehende Skript bleibt als **Variante V0** (Vergleichsbasis für die Arbeit) unverändert erhalten.

### 6.2 Zusammenführung mit Modul 2 (Nachtragserfassung)

Offene Punkte aus Abschnitt 5 der Projektzusammenfassung:

1. **Einheitlicher Parametername:**
   - Ein einziger Name für die LV-Position in beiden Modulen, z. B. `ZWP_400_LV_Position`, falls freigegeben.
   - Sonst `LV_Positionsnummer` aus der vorhandenen Shared-Parameter-Datei. Der Name `LV_Nummer` entfällt.
   - In beiden Skripten als Eingabe einstellbar machen.
2. **Typ oder Exemplar:**
   - Die Untersuchung spricht für das **Exemplar** (Kapitel 1.4).
   - Damit passt Modul 2 (`01_collect_current_state.py` liest am Exemplar) bereits.
   - Sicherheitshalber sollte es trotzdem „erst Exemplar, dann Typ“ lesen, genau wie die Diagnose.
3. `ElementId.IntegerValue` in Modul 2 durch die sichere Variante ersetzen (wie in `lv_mapping`).

### 6.3 n:1-Zuordnung und Mengenermittlung in Modul 2

**Problem:**
- Modul 2 zählt heute **Elemente je LV-Position**.
- Bei n:1 wäre das falsch. Beispiel: Eine Wetterstation besteht aus 4 modellierten Bauteilen, ist aber **1 Stück** im LV. Das Zählen ergäbe 4 Stück, also eine Scheinmehrung.

**Lösungsvorschlag:**
1. **Mengenfaktor in Tabelle A:**
   - Jede Zuordnung bekommt eine Spalte `Mengenfaktor`.
   - `1` = zählt (Leitbauteil), `0` = zählt nicht (Nebenbauteil eines Sets).
   - Optional sind Zwischenwerte möglich, z. B. `0,5`.
   - Modul 2 rechnet `Menge = Σ Mengenfaktor` statt `Anzahl Elemente`.
2. **Alternativ eine Set-Kennung:**
   - Ein Parameter `LV_Set_ID` (z. B. das RDS-Kennzeichen des Leitbauteils).
   - Modul 2 zählt **verschiedene Set-IDs** statt Elemente.
   - Das ist genauer, aber aufwendiger in der Pflege.
3. **Master-/Unterpositionen:**
   - Bauteile werden der Position zugeordnet, die die **Menge trägt**.
   - **[Annahme]** Das ist die Unterposition. Masterpositionen fassen nur zusammen.
   - Dienstleistungs- und Pauschalpositionen (`DL_`, `FP_`) sind **nicht modellbasiert**. Modul 2 sollte sie ausdrücklich als „nicht aus dem Modell ermittelbar“ kennzeichnen statt als Minderung.
4. **Einheiten ≠ Stück** (z. B. `m` bei Kabeln) laufen über den schon vorgesehenen Mengenparameter (Länge).

**Empfehlung für die Arbeit:** Lösung 1 (Mengenfaktor). Sie ist einfach, transparent und in der Tabelle für jeden prüfbar.

---

## 7. Bewertung und Empfehlung

### 7.1 Gegenüberstellung

| Variante | Aufwand | Zuverlässigkeit | Wartbarkeit | Datenschutz | Eignung Bachelorarbeit |
|---|---|---|---|---|---|
| **V0** Bestand: Modell → handgepflegte CSV, Typparameter | gering (vorhanden) | gering bei schlechter Modellpflege; falsche Ebene bei gegliedertem LV | schlecht (CSV von Hand) | sehr gut | gut als **Vergleichsbasis** |
| **V1** SAP-XLSX direkt + Modell/Produktcode + Abschnittstabelle B, Exemplarparameter | mittel | **hoch** für gepflegte Typen | **gut** (LV ist die Datenbank) | sehr gut | **sehr gut**: Kern des Konzepts |
| **V2** V1 + RDS-Übersetzungstabelle A (lokal „gelernt“ + von Hand) | mittel | hoch, deckt schlecht gepflegte Typen ab | gut | sehr gut | **sehr gut** |
| **V3** V2 + KI-Vorschläge offline mit Freigabe | mittel–hoch | hoch (Mensch gibt frei) | gut | gut (Datenminimierung) | **sehr gut**: zeigt KI kontrolliert eingesetzt |
| **V4** KI zur Laufzeit in Dynamo | hoch | mittel | schlecht (API-Schlüssel, Netz, Modelländerungen) | mittel | gut nur als **Gegenbeispiel** |
| **V5** reiner Textabgleich Kurztext | gering | **niedrig** | mittel | sehr gut | als Gegenbeispiel |

### 7.2 Empfehlung und Stufenplan

**Empfohlen:** V3 als Zielbild, schrittweise aufgebaut. V4 und V5 nur als Vergleich in der Arbeit.

| Stufe | Inhalt | Ergebnis |
|---|---|---|
| **0 – Messen** (jetzt) | Diagnose-Skript in einem echten Projekt laufen lassen | Zahlen zur Datenqualität; Antwort auf „Exemplar oder Typ?“ |
| **1 – Minimalversion** | V1: SAP-XLSX lesen, Modell bzw. Produktcode ↔ Leistungsnummer, Tabelle B, Schreiben an Exemplar, Fehler- und Prüfliste | erste messbare Trefferquote |
| **2 – RDS** | V2: Tabelle A aus gut gepflegten Typen erzeugen und Rest von Hand ergänzen; Widerspruchsprüfung | höhere Abdeckung |
| **3 – KI** | V3: Offline-Skript für KI-Vorschläge mit Cache und Freigabespalte | geringere Handarbeit, messbar |
| **4 – Modul 2** | Parametername vereinheitlichen, Mengenfaktor, Master-/Unterpositionen, Pauschalen kennzeichnen | durchgängige Nachtragserfassung |

### 7.3 Kennzahlen für die Arbeit

Zuerst wird ein **Goldstandard** gebildet: Eine Stichprobe von z. B. 100 Elementen wird von einer Fachperson von Hand der richtigen LV-Position zugeordnet. Daran werden alle Varianten gemessen.

| Kennzahl | Formel | Ziel |
|---|---|---|
| **Abdeckung** | Elemente mit automatisch geschriebener Position ÷ alle Elemente | hoch |
| **Präzision** | richtige automatische Zuordnungen ÷ alle automatischen (am Goldstandard) | ≥ 98 % [Annahme, mit Betreuer abstimmen] |
| **Falschzuordnungsquote** | 1 − Präzision | so klein wie möglich (Fehler kosten Geld im Nachtrag) |
| **Prüfquote** | Elemente auf der Prüfliste ÷ alle | klein, aber nicht auf Kosten der Präzision |
| **Mehrdeutigkeitsquote** | Elemente mit mehreren Kandidaten ÷ alle | zeigt, wie wichtig Tabelle B ist |
| **Widerspruchsquote** | Widerspruch Modell ↔ RDS ÷ Elemente mit beiden Merkmalen | Maß für Pflegequalität |
| **Datenqualität** | Anteil Typen mit Modell; Anteil Elemente mit vollständigem RDS; Anteil Typen mit einheitlichem RDS-Schlüssel; RDS_Code-Gegenprobe | Ausgangslage (aus der Diagnose) |
| **Mengenabgleich** | je LV-Position: Modellmenge (mit Mengenfaktor) vs. LV-Menge | Abweichungen = Nachtragskandidaten |
| **Reproduzierbarkeit** | gleiche Eingabe zweimal → Anteil identischer Ergebnisse | V1–V3: 100 %; V4 messen |
| **Zeitaufwand** | Minuten Handarbeit je 100 Elemente, manuell vs. Variante | zeigt den Nutzen |

---

## 8. Dateien dieser Studie

| Datei | Inhalt |
|---|---|
| `MACHBARKEIT_RDS_LV.md` | diese Studie |
| `ANLEITUNG_DIAGNOSE.md` | Schritt-für-Schritt-Anleitung für das Diagnose-Skript |
| `prototypen/RDS_Diagnose.dyn` | Diagnose-Skript für Dynamo (nur lesen) |
| `prototypen/rds_diagnose.py` | dessen Python-Code zum Nachlesen |
| `prototypen/sap_lv_lesen.py` | XLSX-Leser mit Python-Bordmitteln + Auswertung (Grundlage für Kap. 3) |
| `beispieldaten/SAP_LV_Export_Beispiel_anonymisiert.xlsx` | anonymisierter, teilweise **synthetischer** SAP-Export: gleiche 48 Spalten; Preise fiktiv, interne Kalkulationsspalten = 0, Namen entfernt; Abschnitt 05 (Feldgeräte) frei erfunden, passend zu `lv_mapping/LV_Datenbank.csv` |

Die bestehenden Dateien (`lv_mapping/`, `dynamo/`, `shared_parameters/`) wurden **nicht verändert**.

---

## 9. Annahmen im Überblick

1. Die RDS-Parameter sind Exemplarparameter (aus dem Screenshot abgeleitet).
2. `432` ist die Kostengruppe nach DIN 276, `BT` steht für Temperatursensor, `AZ` ist ein Projektzusatz.
3. Der Aufbau des `RDS_Code` (Reihenfolge der Teile) ist in allen Projekten gleich. Abgeleitet ist er aus *einem* Beispiel.
4. Die LV-Abschnitte (z. B. `04.01` … `04.06`) entsprechen Gebäuden, Anlagen oder Schaltschränken.
5. Bauteile werden Unterpositionen zugeordnet, nicht Masterpositionen.
6. Die Zahl der eindeutigen Kombinationen ist pro Projekt klein (unter 1.000).
7. Die Kostenschätzung beruht auf Listenpreisen (Oktober 2026) und angenommenen Mengen.

---

## 10. Fragen an dich

1. **LV-Gliederung:** Wonach sind die LV-Abschnitte gegliedert (z. B. `04.01` … `04.06` im Beispiel): Gebäude, Anlage, Schaltschrank, Bauabschnitt? Gibt es dafür eine Regel, die sich mit RDS-Werten verbinden lässt?
2. **Langtext:** Kann SAP den Langtext mit exportieren (eigene Spalte)?
3. **RDS im LV:** Gibt es Projekte, in denen das LV oder die SAP-Stückliste RDS-Kennzeichen enthält, also Fall 2?
4. **Modell-Inhalt:** Steht in „Modell“ bei gepflegten Typen die Produktbezeichnung (`QAM2112.040`) oder die Bestellnummer (`S55…`)?
5. **Familien-/Typnamen:** Enthalten sie in euren Bibliotheken die Produktbezeichnung? Ein paar Beispiele würden genügen.
6. **ZWP_400-Parameter:** Wer legt sie an und wofür? Darf das Skript `ZWP_400_LV_Position` beschreiben? Was steuern `ZWP_400_LP8_Abrechnung` und `ZWP_400_Auswahlfilter`?
7. **RDS-Bedeutung:** Gibt es eine Dokumentation der Funktionscodes (z. B. `BTAZ`) und der Systemcodes (`432`, `TKA`)? Damit ließen sich die Annahmen in 1.2 belegen.
8. **Masterpositionen:** Wird bei M/U-Positionen nach Master oder nach Unterposition abgerechnet bzw. gezählt?
9. **KI-Freigabe:** Welche KI und welcher Zugang sind bei Siemens freigegeben? Gibt es Vorgaben, welche Daten (z. B. Preise) nicht hinausgehen dürfen?
10. **Goldstandard:** Kann eine Fachperson für eine Stichprobe (ca. 100 Elemente) die richtige LV-Position von Hand festlegen?
