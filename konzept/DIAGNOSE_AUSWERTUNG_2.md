# Auswertung GA-Diagnose Nr. 2 – echtes Projektmodell, 8 Kategorien

> **Datengrundlage:** Lauf von `GA_Diagnose.dyn` am 13.10.2026 im Planermodell, alle Dateien 0–4, 6 und 7. Eine LV-Datei war nicht angegeben, deshalb gibt es keine Dateien 5.
>
> **Abgrenzung:** Parameter und Filter des Planers (Präfix `ZWP_`) gehören nicht zur Siemens-Leistung und werden **nicht ausgewertet** (Vorgabe des Anwenders). Das Diagnose-Skript ignoriert sie ab sofort.
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
| Ansichtsfilter | 322, **alle vom Planer** |
| Worksharing | ja; von anderen Benutzern belegt: 0 |

---

## 2. Befunde

| Nr. | Befund | Zahlen |
|---|---|---|
| B1 | **Kostengruppe:** Außerhalb der Planerparameter gibt es zwei Kostengruppen-Parameter. | `Kostengruppe` (Typ): 318 Elemente mit Wert; `DIN 276` (Exemplar): an 17.004 Elementen vorhanden, aber leer |
| B2 | **Der Arbeitssatz trennt die Gewerke.** In `480_Gebäudeautomation` liegen mindestens 1.984 Elemente. Die Zahl ist eine Untergrenze, weil die Datei je Kategorie nur die drei häufigsten Arbeitssätze nennt. Weitere Arbeitssätze: `450_Nachrichtentechnik`, `456_Sicherheitstechnik`, `440_Starkstrom`, `440_Bodentanks`, `444_Elektrotrassen` | Elektrische Ausstattung 919, Elektroinstallationen 583, HLS-Bauteile 327, Brandmelder 110, Datengeräte 43, Kommunikationsgeräte 2 |
| B3 | **RDS-System 48x** haben nur 1.396 Elemente. Feldgeräte an Lüftungs-, Heizungs- und Kälteanlagen tragen die Kostengruppe **der Anlage** (432 TKA, 422 HZK, 434 KKR). Das RDS-System allein unterschätzt den GA-Umfang also. | Elektrische Ausstattung 691, Elektroinstallationen 455, HLS-Bauteile 111, Brandmelder 110, Datengeräte 27, Kommunikationsgeräte 2 |
| B4 | **„Siemens-typisch“ (57 %) ist zu grob**, und zwar in zwei Richtungen. Erstens kennzeichnet `SI_` die Siemens-**Familienbibliothek**, nicht Siemens-Produkte. Zweitens sind Siemens-Produkte nicht automatisch GA. | Sicherheitsgeräte: 82 % `SI_`-Familien, aber **0 %** Siemens-Produktcodes. Brandmelder: 100 % Siemens-Produkte, aber im Arbeitssatz `450_Nachrichtentechnik` mit RDS `456 BMA`. |
| B5 | **32 % aller Elemente sind verschachtelt**, in drei sehr unterschiedlichen Arten (Kapitel 3). | 5.677 von 17.835 |
| B6 | **Im GA-Arbeitssatz haben die Siemens-Produktfamilien durchgehend „Modell“.** Ohne „Modell“ sind dort nur etwa vier Generik-Typen des Planers (Raumautomationsverteiler 166, Automationsschwerpunkt 39, Sensorsymbol 27, Schaltschrank 2). | Die Typ-Tabelle T2 wäre für GA sehr klein [Annahme] |
| B7 | **Datenqualität:** Es gibt Platzhalter in „Modell“ (`XXX`, `Typ X`, `A`, `Z`), einen Tippfehler (`phsyischer Datenpunkt`) und einen Widerspruch zwischen Typname und Modell (`RL 512/23` ↔ `RL 521/23`). Bei Unterfamilien hängt oft eine Beschreibung am Modell. | Solche Fälle landen auf der Prüfliste |
| B8 | **Abbruchphase** ist nirgends gesetzt. Phasen werden nicht für „entfallen“ genutzt. | 0 |
| B9 | **Es gibt keine Änderungsparameter.** `Änderungsart`, `Änderungsdatum` und `Nachtragsnummer` kommen in diesem Planermodell nicht vor. | 0 (in `3_Parameter.csv` nicht vorhanden) |
| B10 | **78 Modellnamen fehlen in der Datenbank.** Das ist erwartbar, denn die Test-Datenbank hat nur 4 Einträge. Mit dem SAP-LV wird die Liste aussagekräftig. | – |

---

## 3. Verschachtelte Bauteile: drei Arten

Die Regel „verschachtelte Bauteile nie zählen“ ist **zu grob**. **[Befund]**

| Art | Beispiele | Anzahl | Richtig zählen? |
|---|---|---|---|
| **A – eigenes Produkt** | Meldersockel `FDB221` im Rauchmelder; Rauchmelder `FDOOT241-A`; Gehäuse `FDCH221`; Jalousieaktor und -antrieb | 1.961 + 1.955 + 167 + 160 | **möglicherweise ja**: Ein Sockel ist im LV oft eine eigene Position **[Annahme]** |
| **B – Doppelung des Hauptprodukts** | `QAM2112.040` als Unterfamilie im Kanalfühler (36). `QMX3.P30` als Unterfamilie in **allen** QMX3-Raumbediengeräten (215), obwohl nur 70 echte QMX3.P30 im Modell sind. | 36 + 215 | **nein** |
| **C – Symbol ohne Produkt** | „physischer Datenpunkt“, Kamera-2D-Symbol, Bodentank-Element ohne Modell | 58 + 29 + 985 | **nein** |

**Neue Regel:**
- Ein verschachteltes Bauteil zählt nur, wenn sein Modell ein **anderes** Produkt ist als das des übergeordneten Bauteils **und** dieses Produkt im LV steht.
- Entschieden wird einmal je Unterfamilien-Typ über den Mengenfaktor in T2.
- Grundlage ist die neue Datei `9_Verschachtelung.csv`.

---

## 4. Verknüpfungen (Datei 6)

- Alle **20 Verknüpfungen waren nicht geladen**. Deshalb lässt sich über ihren Inhalt nichts sagen. Alle 17.835 Elemente liegen im geöffneten Modell. **[Befund]**
- Die Verknüpfungen sind:
  - Architekturmodelle (zwei Gebäudeteile),
  - TGA-Modelle je Geschoss, jeweils als RVT und als IFC-Kopie,
  - ein Modell „Gastro und MAB“,
  - ein Küchen-IFC,
  - **ein Modell „MSR_Atrium_Komponenten“**.
- **MSR** steht für Mess-, Steuer- und Regeltechnik, also GA. Dieses Modell könnte GA-Bauteile enthalten, die nicht im geöffneten Modell liegen. **[Annahme]**
- **Prüfung:**
  - In Revit unter „Verwalten“ → „Verknüpfungen verwalten“ nur dieses Modell **neu laden**.
  - Danach die Diagnose nur mit diesem einen Modell laufen lassen.
  - Die Datei 6 zeigt dann, wie viele Elemente darin liegen.

---

## 5. Ansichtsfilter (Datei 7)

- Alle **322 Filter stammen vom Planer**. Sie blenden ausschließlich nach Gewerk, Rohr- und Luftsystem, Familie bzw. Typ und Arbeitssatz aus. 289 davon blenden in mindestens einer Ansicht etwas aus. **[Befund]**
- **Kein einziger Filter arbeitet mit einem Änderungsstatus** wie „gelöscht“, „entfallen“ oder einer Nachtragsnummer. Das deckt sich mit B8 und B9.
- **Antwort auf die offene Frage „Nach welchem Parameter arbeiten die Ausblend-Filter?“:**
  - Im Planermodell gibt es **keinen** Filter für entfallene Bauteile.
  - Entfallen wird nach der **Siemens-Praxis** abgebildet: Projektparameter `Änderungsart` mit dem Wert „gelöscht“ bzw. „entfernt“ und einem passenden Filter (siehe Besprechung, Konzept Kapitel 2.2 und 6.4).
- Ab sofort listet die Diagnose Planerfilter (`ZWP_…`) nicht mehr auf, sondern nur noch eigene Filter.

---

## 6. Was das für den Umfang bedeutet

- **Grobe Größenordnung [Annahme]:** Rund 2.000 der 17.835 Elemente (≈ 11 %) gehören zur GA (Arbeitssatz 480).
- **Bestes Umfangskriterium im Modell [Annahme]:** der Arbeitssatz `480_Gebäudeautomation`. Das RDS-System allein unterschätzt den Umfang (B3), „Siemens-typisch“ ist unscharf (B4).
- **Endgültig entscheidet das LV.** Ob Siemens hier auch Brandmeldeanlage oder Sicherheitstechnik liefert, kannst nur du beantworten.

---

## 7. Erweiterung der Diagnose

Getestet nur im Mock, **Test in echtem Revit steht aus**:

| Änderung | Zweck |
|---|---|
| `ZWP_`-Parameter und -Filter werden ignoriert | Trennung von Planerdaten |
| `8_Werte.csv`: Werte je Kategorie für Arbeitssatz, `Kostengruppe`, `DIN 276`, `Gewerk`, `Änderungsart`, `Änderungsdatum`, `Nachtragsnummer`, `Nachtragsbezeichnung`, `Phase erstellt`, `Phase abgebrochen`, RDS_System | Arbeitssatz vollständig (nicht nur Top 3), Änderungsdokumentation, Phasen |
| `9_Verschachtelung.csv`: jede Kombination aus Unterfamilie und übergeordnetem Bauteil mit „gleiches Produkt?“ und „im LV?“ | Kapitel 3 |
| `1_Kategorien.csv`: neue Spalten „Änderungsart gefüllt“ und „Nachtragsnummer gefüllt“ | Abgleich mit der Änderungsdokumentation |
