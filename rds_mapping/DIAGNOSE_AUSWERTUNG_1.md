# Auswertung RDS-Diagnose Nr. 1 – echtes Projektmodell

> **Datengrundlage:** Ein Lauf von `RDS_Diagnose.dyn` im echten Revit-Projektmodell des Anwenders (Oktober 2026). Ausgewertet wurden die Dateien `1_Elemente.csv`, `2_Typen.csv` und `3_Parameter.csv`.
>
> **Datenschutz:** Die Rohdaten liegen **nicht** im (öffentlichen) Repository. Hier stehen nur zusammengefasste Zahlen.
>
> **Bezug:** Diese Auswertung prüft die Annahmen aus `MACHBARKEIT_RDS_LV.md`.

---

## 1. Umfang

| | Elemente | Typen |
|---|---|---|
| **Gesamt** | **10.882** | **143** |
| Kabeltrassenformteile | 6.758 | |
| Kabeltrassen | 1.837 | |
| Elektrische Ausstattung | 1.351 | |
| HLS-Bauteile | 831 | |
| Elektrischer Stromkreis (ohne Typ) | 105 | |

Nach Familienart gruppiert:

| Gruppe | Elemente | Typen | „Modell“ gefüllt | RDS_Code gefüllt | echte RDS-Funktion |
|---|---|---|---|---|---|
| **Siemens-Produktfamilien** (`SI_…`, `SIE_…`) | 1.322 | 40 | **1.321 (≈ 100 %)** | 1.316 | 1.253 |
| Projekt-/Generikfamilien (`ZWP_…`: Schaltschränke, Verteiler, Brandschotts, Trassentypen) | 2.201 | 63 | **0** | 886 | 347 |
| Trassenzubehör von Herstellern (Stiele, Ausleger, Schutzkappen, Gewindestangen) | 7.253 | 38 | **0** | 5.866 | 0 (nur Platzhalter `____`) |
| Elektrische Stromkreise | 105 | – | – | – | – |

---

## 2. Die Annahmen der Studie im Abgleich

| Nr. | Annahme / Aussage der Studie | Ergebnis | Beleg |
|---|---|---|---|
| A1 | RDS-Parameter sind **Exemplarparameter** | **bestätigt** | Bei allen RDS-Parametern liegt der Fundort bei 10.777 bzw. 10.882 Elementen auf „nur Exemplar“. Ausnahme: 16–18 Elemente einer Familie (Fluchttürzentrale), die zusätzlich gleichnamige *Typ*parameter hat. |
| A2 | „Modell“ ist **schlecht gepflegt** | **widerlegt für Produkte**, zutreffend nur für Nicht-Produkte | Siemens-Produktfamilien: 1.321 von 1.322 gefüllt. Leer ist „Modell“ nur bei Generikfamilien und Trassenzubehör. Diese haben ohnehin keine Siemens-Leistungsnummer. |
| A3 | Der RDS-Schlüssel (System + Funktion) ist **nicht typbezogen** | **bestätigt** | 16 von 40 Siemens-Typen (648 von 1.322 Elementen) haben innerhalb eines Typs mehrere RDS-Schlüssel. Beispiel: Kanalfühler `QAM2112.040` kommt in **10** verschiedenen Kombinationen vor (Funktionen BTAA, BTAL, BTAO, BTAU, BTAZ in den Systemen ABA, TKA, ULA, ZUA). |
| A4 | Ein RDS-Schlüssel führt **nicht** immer zu genau einem Produkt | **bestätigt** | 11 von 52 Schlüsseln (System \| Funktion) gehören zu mehreren Produkten, z. B. `HZK\|BTAR` → `QAE2112.010`, `QAE2112.015`, `QAD2012`. Nur **882 von 1.253** Elementen (70 %) hätten über das RDS allein ein eindeutiges Produkt. Mit der Funktion allein (ohne System) ist es noch unschärfer (z. B. `BTAB` → 5 Produkte). |
| A5 | `RDS_Code` passt zu den Einzelparametern (Aufbau aus einem Beispiel abgeleitet) | **bestätigt, soweit prüfbar** | 1.596 × „ja“, **0 × „nein“**. Bei 9.286 Elementen „unbekannt“, weil `RDS_FunktionsNum` fehlt (siehe 3.4). |
| A6 | `ZWP_400_LV_Position` eignet sich als Ziel | **technisch ja** | Exemplarparameter, Datentyp Text, an 10.777 Elementen vorhanden (alle außer Stromkreisen), überall **leer**. Ob der ZWP-Prozess das Beschreiben erlaubt, ist weiterhin offen. |
| A7 | Ort/Anlage entscheidet über den LV-Abschnitt | **teilweise belegt** | Gebäude, Bauabschnitt, Modul und Teilmodul sind bei **allen** Siemens-Elementen gleich. Unterscheiden lassen sich die Elemente nur über System + Anlagennummer (148 verschiedene Kombinationen, z. B. `TKA.01`, `TKA.02`, `TKA.03`) sowie über Geschoss/Segment. Ob das LV so gegliedert ist, bleibt Frage 1. |

**Folge für die Studie:**

1. **Das Produkt bestimmt man über „Modell“, nicht über das RDS.**
   - „Modell“ ist bei allen Siemens-Produkten vorhanden.
   - Das RDS ist als Produktschlüssel zu unscharf (A3, A4).
   - Stufe 3 der Kaskade („Tabelle A aus RDS“) wird damit für Siemens-Produkte **kaum gebraucht**.
2. **Das RDS ist der Ortsschlüssel.**
   - Es dient zur Wahl des LV-Abschnitts über System + Anlagennummer (Tabelle B).
   - Dort ist es gut gepflegt: `RDS_System` 97 %, `RDS_Systemkennzeichnung` 94 %.
3. **Nicht-Produkte brauchen einen eigenen Weg.** Generikfamilien und Trassen machen 87 % der Elemente aus (Kapitel 3.1).

---

## 3. Neue Befunde, die die Studie noch nicht berücksichtigt

### 3.1 Trassen und Generikfamilien: der Typname ist der Schlüssel

- Die Typnamen sind **systematisch aufgebaut**:
  - `ZWP_440_Kabelrinne_E90`
  - `ZWP_450_Kabelleiter`
  - `480_Kabelrinne`
- Sie enthalten:
  - die Kostengruppe (**[Annahme]** DIN 276: 440 Starkstrom, 450 Kommunikations-/Sicherheitstechnik, 480 Gebäudeautomation)
  - die Bauart
  - den Brandschutz (E30/E90/I30/I90)
- Das sind nur **101 Typen** (63 + 38). Eine kleine Tabelle „Familie/Typ → Leistungsnummer bzw. LV-Kurztext“ ist von Hand in kurzer Zeit machbar. Eine KI wird dafür nicht gebraucht.
- **Mengen:**
  - Kabeltrassen werden im LV vermutlich in **Metern** abgerechnet. Die Menge ist dann die Länge, nicht die Stückzahl.
  - Formteile und Zubehör sind vermutlich im Meterpreis enthalten → Mengenfaktor 0.
  - Allein die Kategorie „Kabeltrassenformteile“ umfasst 6.758 Elemente: Bögen und T-Stücke, aber auch Stiele, Ausleger, Schutzkappen und Gewindestangen. Würde man sie stückweise zählen, wäre das Ergebnis völlig verfälscht.
  - **[Offen]**

### 3.2 Verschachtelte Unterfamilien → Doppelzählung droht

- **69 Elemente** gehören zu Familien mit `_UF_` im Namen, z. B. `SIE_DE_COM_UF_QAM2112.040` oder `SI_DE_UF_Anlegetemperaturfühler_QAD2012`.
- Zu jeder gibt es eine Hauptfamilie mit **gleicher Stückzahl**: QAM2112.040 36 + 36, QPM1104 17 + 17, QAD2012 8 + 8.
- Beide liegen im gleichen Segment und an der gleichen Anlage.
- Die UF-Elemente haben bei „Modell“ einen Beschreibungstext (`QAM2112.040  Temperatur PT1000 0.4m(0)`) und **keine** RDS-Funktion.
- **[Annahme]** „UF“ steht für *Unterfamilie*. Es handelt sich um geteilte, verschachtelte Familien, die Revit als eigene Elemente zählt.
- **Folge:** Ohne Filter würde **jeder** dieser Fühler **doppelt** gezählt: einmal als Hauptfamilie, einmal als Unterfamilie. Für Modul 2 hieße das: Scheinmehrungen.
- **Gegenmaßnahme:**
  - Verschachtelte Elemente erkennen (Revit: „übergeordnetes Element“).
  - Sie bei der Mengenermittlung ausschließen, also Mengenfaktor 0.
  - Das Diagnose-Skript ist dafür ergänzt: neue Spalten „Verschachtelt in (Element-ID)“ und „Familie des übergeordneten Elements“. Damit lässt sich die Annahme beim nächsten Lauf belegen.

### 3.3 „Modell“ muss vor dem Vergleich normalisiert werden

Beispiele aus dem Modell:

| Typname | Modell | Problem |
|---|---|---|
| `QAM2112.040  Temperatur PT1000 0.4m(0)` | gleich | Beschreibung hängt am Produktcode |
| `Telenot VT160` | `VT 160` | Typname und Modell weichen ab, Leerzeichen im Code |
| `UP 258D12` | `UP 258D12` | Leerzeichen im Code |
| `Sivacon Intrusion PRO/ ADV` | `Sivacon Intrusion Pro IO4` | kein klarer Produktcode |

Vorschlag für den Abgleich mit der SAP-`Leistungsnummer`:
- Großschreibung, Leerzeichen entfernen.
- Als Erstes prüfen, ob die Leistungsnummer **am Anfang** von „Modell“ steht (Präfix-Treffer). Damit trifft `QAM2112.040  Temperatur…` auf `QAM2112.040`.

Außerdem gilt:
- In 29 von 41 Siemens-Typen steckt der Produktstamm auch im **Familiennamen** (z. B. `…_Kanaltemperaturfühler_QAM2112`). Bei Siemens-Typen ist zudem der **Typname meist identisch mit „Modell“**.
- Fehlt „Modell“, ist der Typname daher ein guter Ersatz. Stufe 2 der Kaskade ist damit belegt.

### 3.4 Weitere Datenqualitätsbefunde

- **`RDS_FunktionsNum`** ist nur in 2 Kategorien angelegt (Elektrische Ausstattung, HLS-Bauteile). Bei den Trassen fehlt der Parameter, gefüllt ist er nur zu 15 %. Für die Zuordnung ist das unkritisch, weil die Zählnummer ohnehin entfällt.
- **Doppelt vergebene RDS-Codes:** 15 Codes sind bei Siemens-Elementen mehrfach vergeben (35 Elemente). Ein RDS-Kennzeichen sollte eindeutig sein. Das ist eine Kennzahl für die Pflegequalität.
- **`ZWP_400_LP8_Abrechnung`** (Ja/Nein) ist überall angelegt, aber nirgends gesetzt. **`ZWP_400_Auswahlfilter`** gibt es nur bei HLS-Bauteilen (831), und er ist leer.
- **`LV_Nummer`**: Typparameter an allen Typen. 72 Elemente (2 Typen) tragen Testwerte (`03.01.06test`, `03.02.06test`). Das heißt: `lv_mapping` hat im echten Revit geschrieben. Die Testwerte sollten vor dem Produktiveinsatz wieder entfernt werden.
- **Elektrische Stromkreise** (105) haben keinen Typ und gehören nicht zur Zuordnung. Diese Kategorie künftig nicht anhaken.

---

## 4. Angepasste Empfehlung

Die Kaskade aus Kapitel 2 der Studie wird nach **Elementgruppe** aufgeteilt:

| Gruppe | Anteil | Produktschlüssel | Ortsschlüssel (LV-Abschnitt) | Menge |
|---|---|---|---|---|
| Siemens-Produkte | 12 % | „Modell“ (normalisiert, Präfix) → SAP-`Leistungsnummer`; Ersatz: Typname | RDS System + Anlagennummer (Tabelle B) | Stück; **verschachtelte Unterfamilien ausschließen** |
| Generikfamilien (Schaltschränke, Verteiler, Brandschotts …) | 20 % | Tabelle „Familie/Typ → Leistungsnummer“ (von Hand, 63 Typen) | wie oben | Stück |
| Trassen und Zubehör | 67 % | Tabelle „Typ → Leistungsnummer“ (von Hand, 38 + Trassentypen) | Kostengruppe aus dem Typnamen (440/450/480) | **Länge** in m; Formteile/Zubehör Mengenfaktor 0 [Offen] |

**KI:** Durch diese Befunde wird der Bedarf noch kleiner. Für Siemens-Produkte genügt „Modell“. Für die übrigen rund 100 Typen ist eine Handtabelle schneller als eine KI-Prüfschleife. Die KI (Variante a) bleibt sinnvoll für:
- den Vorschlag der Typ-Tabelle, wenn die Typnamen weniger sprechend sind,
- Modelle mit tausenden Typen.

**Nächster Schritt:** Ein **SAP-Export des LV zu genau diesem Projekt**. Erst damit lassen sich messen:
- Trefferquote „Modell ↔ Leistungsnummer“
- LV-Gliederung (Frage 1)
- Meter-Abrechnung der Trassen

---

## 5. Neue bzw. präzisierte Fragen

1. **Kostengruppen im LV:** Gehören die Kostengruppen 440 (Starkstrom) und 450 (Kommunikation/Sicherheit) zu deinem LV oder nur 480 (Gebäudeautomation)? Davon hängt ab, welche Kategorien und Typen überhaupt zugeordnet werden müssen.
2. **Trassen:** Werden Kabeltrassen im LV nach Metern abgerechnet? Sind Formteile (Bögen, T-Stücke) und Zubehör (Stiele, Ausleger, Gewindestangen) eigene Positionen oder im Meterpreis enthalten?
3. **Unterfamilien:** Bestätigst du, dass „UF“ für verschachtelte Unterfamilien steht? Am einfachsten lässt sich das mit einem zweiten Diagnoselauf prüfen, der die neue Spalte „Verschachtelt in“ enthält.
4. **Projekt-LV:** Kannst du den SAP-Export des LV **zu diesem Projekt** bereitstellen? Er wird nur lokal ausgewertet und nicht ins öffentliche Repository gelegt.
5. Die Fragen 1, 6, 8 und 9 aus der Studie sind weiterhin offen:
   - LV-Gliederung
   - ZWP-Prozess
   - Master-/Unterpositionen
   - KI-Freigabe
