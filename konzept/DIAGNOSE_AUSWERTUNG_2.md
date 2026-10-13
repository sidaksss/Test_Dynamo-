# Auswertung GA-Diagnose Nr. 2 – echtes Projektmodell, 8 Kategorien

> **Datengrundlage:** Lauf von `GA_Diagnose.dyn` am 13.10.2026 im Planermodell. Ausgewertet sind die Dateien 0–4. Die Dateien 6 (Verknüpfungen) und 7 (Filter) stehen noch aus. Eine LV-Datei war nicht angegeben, deshalb gibt es keine Dateien 5.
>
> **Datenschutz:** Hier stehen nur zusammengefasste Zahlen. Die Rohdaten liegen nicht im öffentlichen Repository.
>
> **Kennzeichnung:** **[Befund]** = aus den Daten; **[Annahme]** = Deutung, nicht belegt.

---

## 1. Umfang des Laufs

| | |
|---|---|
| Kategorien | Brandmelder, Datengeräte, Elektrische Ausstattung, Elektroinstallationen, HLS-Bauteile, Kommunikationsgeräte, Notrufgeräte, Sicherheitsgeräte |
| Elemente / Typen / eindeutige Kombinationen | **17.835 / 215 / 789** |
| Dauer | 144 s |
| Verknüpfungen | 20, davon **0 geladen** |
| Ansichtsfilter | 322 |
| Worksharing | ja; von anderen Benutzern belegt: 0 |

---

## 2. Befunde

| Nr. | Befund | Zahlen |
|---|---|---|
| B1 | **`ZWP_400_LP8_Abrechnung` ist nirgends angehakt.** Auch `ZWP_400_LV_Position` und `ZWP_400_LV_Text` sind leer. | LP8: 0 von 17.830; LV_Position: 0 von 17.835; LV_Text: 0 von 7.543 |
| B2 | **`ZWP_400_Freigegeben` ist ebenfalls nirgends gesetzt** und gibt es nur bei HLS-Bauteilen. **Korrektur:** Im Screenshot sah das Häkchen gesetzt aus. In Revit zeigt ein **grau** dargestelltes Häkchen aber einen Ja/Nein-Parameter **ohne Wert** an. Dasselbe gilt für LP8. | 0 von 831 |
| B3 | **Es gibt drei Kostengruppen-Parameter.** | `ZWP_400_Kostengruppe` (Typ): 7.586 von 17.835 mit Wert (43 %); `Kostengruppe` (Typ): 318; `DIN 276` (Exemplar): an 17.004 vorhanden, aber leer |
| B4 | **Der Arbeitssatz trennt die Gewerke.** In `480_Gebäudeautomation` liegen mindestens 1.984 Elemente. Die Zahl ist eine Untergrenze, weil die Datei je Kategorie nur die drei häufigsten Arbeitssätze nennt. Weitere Arbeitssätze: `450_Nachrichtentechnik`, `456_Sicherheitstechnik`, `440_Starkstrom`, `440_Bodentanks`, `444_Elektrotrassen` | Elektrische Ausstattung 919, Elektroinstallationen 583, HLS-Bauteile 327, Brandmelder 110, Datengeräte 43, Kommunikationsgeräte 2 |
| B5 | **RDS-System 48x** (Kostengruppe 480) haben nur 1.396 Elemente. Feldgeräte an Lüftungs-, Heizungs- und Kälteanlagen tragen die Kostengruppe **der Anlage** (432 TKA, 422 HZK, 434 KKR), obwohl sie zur GA gehören. Das RDS-System allein unterschätzt den GA-Umfang also. | Elektrische Ausstattung 691, Elektroinstallationen 455, HLS-Bauteile 111, Brandmelder 110, Datengeräte 27, Kommunikationsgeräte 2 |
| B6 | **„Siemens-typisch“ (57 %) ist zu grob**, und zwar in zwei Richtungen. Erstens kennzeichnet `SI_` die **Siemens-Familienbibliothek**, nicht Siemens-Produkte. Zweitens sind Siemens-Produkte nicht automatisch GA. | Sicherheitsgeräte: 82 % `SI_`-Familien, aber **0 %** Siemens-Produktcodes (Kameras, Lautsprecher und Zutrittstechnik anderer Hersteller). Brandmelder: 100 % Siemens-Produkte (FDOOT241, FDB221), aber im Arbeitssatz `450_Nachrichtentechnik` mit RDS `456 BMA`, also Brandmeldeanlage und nicht KG 480. |
| B7 | **32 % aller Elemente sind verschachtelt.** Dahinter stecken drei sehr unterschiedliche Arten (Kapitel 3). | 5.677 von 17.835 |
| B8 | **Im GA-Arbeitssatz haben die Siemens-Produktfamilien durchgehend „Modell“.** Ohne „Modell“ sind dort nur wenige Generik-Typen: `ZWP_480_RAV_Raumautomationsverteiler` (166), `ZWP_480_Automationsschwerpunkt` (39), `ZWP_480_Sensorik_Symbol` (27), `ZWP_480_ALL_Schaltschrank` (2). | Die Typ-Tabelle T2 wäre für GA sehr klein (einstellige Zahl an Typen) [Annahme] |
| B9 | **Datenqualität:** Es gibt Platzhalter in „Modell“ (`XXX`, `Typ X`, `A`, `Z`), einen Tippfehler (`phsyischer Datenpunkt`) und einen Widerspruch zwischen Typname und Modell (`RL 512/23` ↔ `RL 521/23`). Bei Unterfamilien hängt oft eine Beschreibung am Modell (`QMX3.P30  Temperaturfühler Wandmontage(0)`). | Solche Fälle landen auf der Prüfliste |
| B10 | **`ZWP_400_LV_Aufteilung`** ist ein Exemplarparameter mit Wert bei 10.042 Elementen. Der Inhalt ist noch unbekannt. Möglicherweise ist es die LV-Aufteilung des Planers (Los oder Gewerk). Das wäre ein starkes Umfangskriterium. | Inhalt zeigt die erweiterte Diagnose (`8_Werte.csv`) |
| B11 | **Die Verknüpfungen waren nicht geladen.** Über ihren Inhalt lässt sich nichts sagen. Alle 17.835 Elemente liegen im **geöffneten** Modell. | – |
| B12 | **Abbruchphase** ist nirgends gesetzt. Phasen werden also nicht für „entfallen“ genutzt. | 0 |
| B13 | **78 Modellnamen fehlen in der Datenbank.** Das ist erwartbar, denn die Test-Datenbank hat nur 4 Einträge. Mit dem SAP-LV wird diese Liste aussagekräftig. | – |

---

## 3. Verschachtelte Bauteile: drei Arten

Die Regel „verschachtelte Bauteile nie zählen“ aus dem Konzept ist **zu grob**. **[Befund]**

| Art | Beispiele | Anzahl | Richtig zählen? |
|---|---|---|---|
| **A – eigenes Produkt** | Meldersockel `FDB221` im Rauchmelder; Rauchmelder `FDOOT241-A`; Gehäuse `FDCH221`; Jalousieaktor und -antrieb (UF1/UF2) | 1.961 + 1.955 + 167 + 160 | **möglicherweise ja**: Ein Meldersockel ist im LV oft eine eigene Position **[Annahme]** |
| **B – Doppelung des Hauptprodukts** | `QAM2112.040` als Unterfamilie im Kanalfühler (36). Raumbediengerät `QMX3.P30` als Unterfamilie in **allen** QMX3-Raumbediengeräten (215), obwohl nur 70 echte QMX3.P30 im Modell sind (die übrigen 145 stecken in P37, P02, P70, P34). | 36 + 215 | **nein**: würde 215 Raumbediengeräte QMX3.P30 statt 70 ergeben |
| **C – Symbol ohne Produkt** | „physischer Datenpunkt“, Kamera-2D-Symbol, `ZWP_440_BT_Element` (ohne Modell) | 58 + 29 + 985 | **nein** |

**Neue Regel (Vorschlag):**
- Ein verschachteltes Bauteil zählt nur, wenn sein Modell ein **anderes** Produkt ist als das des übergeordneten Bauteils **und** dieses Produkt als Leistungsnummer **im LV** steht.
- Die Entscheidung fällt einmal je Unterfamilien-Typ über den Mengenfaktor in der Typ-Tabelle T2.
- Die neue Datei `9_Verschachtelung.csv` liefert dafür je Kombination aus Unterfamilie und übergeordnetem Bauteil:
  - die Anzahl,
  - „gleiches Produkt wie übergeordnet?“,
  - „Modell im LV?“.

---

## 4. Was das für den Umfang bedeutet

- **Grobe Größenordnung [Annahme]:** Rund 2.000 der 17.835 Elemente (≈ 11 %) gehören zur GA (Arbeitssatz 480). Die übrigen gehören zu Brandmeldeanlage, Sicherheitstechnik, Starkstrom, Nachrichtentechnik und Trassen.
- **Bestes Umfangskriterium [Annahme]:** Arbeitssatz `480_Gebäudeautomation`, ggf. ergänzt um `ZWP_400_LV_Aufteilung` und `ZWP_400_Kostengruppe`.
  - Das RDS-System allein unterschätzt den Umfang (B5).
  - Das Kriterium „Siemens-typisch“ ist unscharf (B6).
- **Endgültig entscheidet das LV:** Was Siemens laut LV ausführt, gehört dazu. Ob Siemens hier auch Brandmeldeanlage oder Sicherheitstechnik liefert (eigenes LV?), kannst nur du beantworten.

---

## 5. Erweiterung der Diagnose

Zwei neue Dateien, Test nur im Mock, **Test in echtem Revit steht aus**:

| Datei | Inhalt | beantwortet |
|---|---|---|
| `8_Werte.csv` | Je Kategorie: Werte und Anzahl für Arbeitssatz, `ZWP_400_LV_Aufteilung`, `ZWP_400_Kostengruppe`, `ZWP_400_Gewerk`, `Gewerk`, `Kostengruppe`, `DIN 276`, `ZWP_450_Ausführungsart`, `ZWP_400_Listenfilter`, `ZWP_400_Freigegeben`, LP8, RDS_System. Jeweils mit „davon Siemens-Produktcode“, „davon RDS 48x“ und „davon verschachtelt“. | B4 vollständig (nicht nur Top 3), B10, Kostengruppen-Werte |
| `9_Verschachtelung.csv` | jede Kombination aus Unterfamilie und übergeordnetem Bauteil, mit Modell beider, Anzahl, „gleiches Produkt?“, „im LV?“ | Kapitel 3 |

---

## 6. Offene Punkte aus diesem Lauf

1. Bitte noch `6_Verknuepfungen.csv` und `7_Filter.csv` schicken.
2. Gehören **Brandmeldeanlage** (Melder `FDOOT241`, Sockel `FDB221`) und **Sicherheitstechnik** (Zutritt, Einbruch, Video) zum Siemens-LV dieses Projekts oder nur die GA?
3. Was bedeutet `ZWP_400_LV_Aufteilung`? Die erweiterte Diagnose zeigt die Werte.
4. Für den nächsten Lauf: SAP-LV als `.xlsx` angeben, damit die Dateien 5 und die Spalte „im LV“ in Datei 9 entstehen.
