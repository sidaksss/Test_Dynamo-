# KI-Einbindung in das Dynamo-Konzept: Nutzen, Technik, Nachweis

> **Zweck:** Entscheidungsgrundlage, an welchen Stellen eine KI **messbar** mehr leistet als feste Regeln oder reines Python, und wie sie technisch sicher eingebunden wird.
>
> **Status:**
> - Der Prototyp `ki_zuordnung_prototyp.py` ist nur im **Testmodus** mit festen Beispielantworten getestet.
> - **Tests mit echtem API-Zugang und in echtem Revit stehen bei dir aus.**
> - Bestehende Dateien wurden nicht verändert.
>
> **Kennzeichnung:**
> - **[Beleg]**: aus Projektdaten, Diagnosen oder der offiziellen Schnittstellen-Dokumentation.
> - **[Annahme]**: Einschätzung, nicht belegt.
> - **[Offen]**: braucht deine Antwort.

---

## 0. Kurzfazit

1. **Eine KI lohnt sich nur dort, wo der Sinn von Freitext verstanden werden muss.** Feste Regeln und Wortvergleiche erkennen das nicht.
   - Das gilt vor allem für die **Zuordnung von Bauteilen ohne gepflegtes „Modell“** zu LV-Positionen.
   - Beispiel aus dem Prototyp: Ein Bauteil heißt „Automationsstation bis 200 Datenpunkte“. Der Wortvergleich wählt die Station „bis 400 DP“. Die richtige Position heißt „< 200 E/A“ und teilt kaum Wörter mit dem Bauteiltext **[Beleg: Testlauf]**.
   - Ob eine KI solche Fälle zuverlässig löst, ist **noch nicht gemessen [Annahme]**.
2. **Keine KI braucht es** für:
   - den Vergleich von Modellständen,
   - Mengen, Preise und Gruppierung,
   - die meisten Plausibilitätsprüfungen,
   - Zusammenfassungen mit Zahlen.

   Dort sind feste Regeln zuverlässiger, schneller, kostenlos und vollständig nachvollziehbar.
3. **Wie groß der Nutzen in deinem Projekt ist, ist offen.** Die Diagnose zeigt: Im GA-Bereich haben die Siemens-Familien „Modell“ fast immer gefüllt, ohne „Modell“ sind dort nur etwa vier Generik-Typen **[Beleg: Diagnose 2]**. Für dieses Projekt wäre der KI-Nutzen also **klein**. Groß wird er in Projekten mit schlecht gepflegtem „Modell“, deiner Ausgangsannahme. Genau das lässt sich mit einem **Ausblendversuch** messen (Kapitel 4).
4. **Empfohlene Technik:** Die KI läuft **einmalig in einem eigenen Schritt** außerhalb des Zuordnungslaufs. Ihr Ergebnis ist eine Übersetzungstabelle mit Vertrauenswert, ein Mensch gibt unsichere Zeilen frei, und Dynamo liest nur freigegebene Zeilen. Ein KI-Aufruf während des Dynamo-Laufs ist technisch möglich, wird aber nicht empfohlen.
5. **Für die Arbeit:** KI als **messbarer Klassifikator mit Vergleichsgruppe** (Regel, Regel + Wortvergleich, Regel + Wortvergleich + KI), nicht als Selbstzweck. Das ist die Sprache der Automatisierungstechnik: Eingang, Ausgang, Fehlerquote, Vergleich mit dem Basisverfahren.

---

## 1. Begriffe kurz erklärt

| Begriff | Bedeutung |
|---|---|
| **KI-Schnittstelle (API)** | Internetadresse, an die ein Programm eine Anfrage schickt und eine Antwort der KI zurückbekommt |
| **API-Schlüssel** | geheimes Kennwort, mit dem sich das Programm bei der Schnittstelle ausweist |
| **Token** | Abrechnungseinheit der KI, etwa ¾ Wort; Kosten entstehen je Token |
| **Festes Antwortschema** | Die KI muss in einem vorgegebenen Format antworten, z. B. nur „K1“ bis „K5“ oder „KEINE“ |
| **Zwischenspeicher (Cache)** | Datei, in der jede Antwort gespeichert wird; dieselbe Frage wird nicht erneut gestellt |
| **Vertrauenswert** | Einstufung HOCH / MITTEL / NIEDRIG, wie sicher eine Zuordnung ist |
| **Referenz (Ground Truth)** | sicher bekannte richtige Antworten, mit denen Ergebnisse gemessen werden |
| **Ausblendversuch** | Man entfernt absichtlich eine bekannte Angabe (z. B. „Modell“) und prüft, ob das Verfahren die Antwort trotzdem findet |
| **Umgebungsvariable** | in Windows hinterlegter Wert, den Programme lesen können, ohne dass er in einer Datei steht |

---

## 2. Bewertung der Einsatzideen

Bewertung: + gering / ++ mittel / +++ hoch; bei Risiko bedeutet mehr + mehr Risiko.

| Nr. | Idee | Nutzen | Aufwand | Risiko | Zuverlässigkeit | Nachvollziehbarkeit | Wiederholbarkeit | Reicht eine Regel bzw. ein Wortvergleich? | Urteil |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Zuordnung Bauteil → LV-Position, wenn „Modell“ fehlt.** Eingabe: Familie, Typ, Kommentar, RDS-Funktion, LV-Kurztext; je Kombination | ++ bis +++ (projektabhängig) | ++ | ++ (falsche Position = falscher Preis) | unbekannt, **messen** | ++ (Begründung je Zeile) | +++ mit Zwischenspeicher | **teilweise**: Regel trifft bei gefülltem Modell sicher; Wortvergleich findet oft den richtigen Kandidaten, scheitert aber an Bedeutung (Beispiel oben) | **empfohlen**, mit Messung |
| 2a | Plausibilität: Regelverstöße (Status ohne Nachtragsnummer, ohne LV-Position, entfällt + sichtbar, Vergleich ↔ Dokumentation) | +++ | + | + | +++ | +++ | +++ | **ja, vollständig** | **keine KI** |
| 2b | Plausibilität: inhaltliche Widersprüche (z. B. RDS-Funktion „Temperatursensor“, gewählte Position „Ventilantrieb“; Kommentar „entfällt“, Status leer) | ++ | ++ | + (meldet nur) | mittel [Annahme] | ++ | +++ mit Zwischenspeicher | **teilweise**: Eine Regeltabelle „RDS-Kennbuchstabe ↔ Produktgruppe“ deckt viel ab. Die KI findet zusätzlich freie Formulierungen. | **optional**; zuerst Regeltabelle |
| 3 | Textentwurf für **neue** Nachtragspositionen (Kurz-/Langtext), Mensch gibt frei | + bis ++ | + | ++ (fachlich falscher Text im Angebot) | mittel | + | + (Text variiert) | **teilweise**: Für Siemens-Produkte liefert SAP schon Kurztexte [Beleg: SAP-Beispiel]. Nur Sonderleistungen brauchen neuen Text. | **optional**, nur Sonderfälle |
| 4 | Freitext in Kommentaren → Geräteart normalisieren | + allein, ++ als Zuarbeit für Nr. 1 | + | + | ++ | ++ | +++ mit Zwischenspeicher | **teilweise**: Eine Synonymliste („Temp.-Fühler“, „TF“ → Temperaturfühler) reicht für häufige Fälle | **nicht eigenständig**, steckt implizit in Nr. 1 |
| 5 | Auswertungsliste als Erläuterungstext für Projektleitung und Vertrieb | + | + | ++ (falsche Zahl im Text) | mittel | + | + | **ja**: Ein Textbaustein mit eingesetzten Zahlen („Nachtrag NT-02: 3 Positionen Mehrung, Summe X €; größte Änderung: …“) ist fehlerfrei | **keine KI**; höchstens Formulierung, Zahlen nie von der KI |
| 6a | Haupt- vs. Nebenbauteil vorschlagen (Mengenfaktor 1/0, z. B. Sockel, Halter, Symbol) aus Familien-/Typnamen | ++ | + | ++ | mittel [Annahme] | ++ | +++ mit Zwischenspeicher | **teilweise**: Diagnose 2 zeigt gemischte Fälle (Sockel = eigenes Produkt, QMX-Unterfamilie = Doppelung) [Beleg] | **interessant**, einmalig je Typ |
| 6b | Zuordnung von Bauteilen einer Masterposition (z. B. Wetterstation aus mehreren Teilen) | + | ++ | ++ | niedrig [Annahme] | + | ++ | selten, besser von Hand | **nicht empfohlen** |
| 6c | Mengen oder Preise berechnen lassen | – | – | +++ | – | – | – | **ja, Rechnung** | **ausdrücklich keine KI** |

**Reihenfolge nach Nutzen je Aufwand:**
1. Nr. 2a: Regeln, keine KI
2. Nr. 1: KI mit Messung
3. Nr. 6a: KI, einmalig je Typ
4. Nr. 2b: Regeltabelle zuerst, KI optional
5. Nr. 3: nur Sonderfälle
6. Nr. 5: Textbaustein ohne KI
7. Nr. 4: Teil von Nr. 1

**Empfohlene Auswahl für die Bachelorarbeit:**
- **Nr. 1** als Kern des KI-Teils, mit Vergleichsmessung (Kapitel 4).
- **Nr. 6a** optional als zweites, kleines Beispiel.
- Alles andere ohne KI, mit Begründung. Das ist eine Stärke der Arbeit: Sie zeigt, **wo KI nicht nötig ist**.

---

## 3. Technische Einbindung

### 3.1 Architekturvarianten

| Kriterium | **a) Einmaliger KI-Schritt → Übersetzungstabelle, Mensch prüft, Dynamo liest nur die Tabelle** | **b) KI-Aufruf zur Laufzeit im Python-Knoten** | **c) lokal ohne Cloud-KI** (Regel + Wortvergleich, Python-Bordmittel) |
|---|---|---|---|
| Zuverlässigkeit im Modell | hoch: nur Freigegebenes wird geschrieben | mittel: Antworten wirken direkt | hoch für Regeltreffer, mittel für Wortvergleich |
| Nachvollziehbarkeit | hoch: Tabelle mit Begründung, Quelle, Freigabe | gering, solange nicht protokolliert wird | hoch |
| Wiederholbarkeit | **hoch**: Tabelle und Zwischenspeicher sind eingefroren | gering ohne Zwischenspeicher | vollständig |
| Antwortzeit im Dynamo-Lauf | keine, Dynamo liest nur eine Datei | Sekunden je Anfrage; Revit ist währenddessen blockiert | keine |
| Netz, Schlüssel, Proxy | nur einmal, an einem Rechner | auf **jedem** Revit-Rechner, bei **jedem** Lauf | nicht nötig |
| Kosten | einmalig je neuer Kombination | je Lauf, ohne Zwischenspeicher erneut | keine |
| Aufwand für einen Laien | gering: Skript starten, Tabelle prüfen | gering in der Bedienung, hoch bei Störungen | gering |
| Eignung für die Arbeit | **sehr gut**: messbar, sauberer Prüfschritt | mäßig | sehr gut als **Vergleichsgruppe** |

**Empfehlung: c → a, in dieser Reihenfolge.**
- Zuerst Regel und Wortvergleich (c). Das ist schon in `lv_mapping` v2 enthalten.
- Nur die **übrig gebliebenen** Kombinationen gehen an die KI (a). Die KI wählt dabei **nur aus den Kandidaten von c**.
- „Einmalig außerhalb von Revit“ heißt nicht zwingend „ohne Dynamo“. Derselbe Python-Code kann in einem **eigenen Dynamo-Graph ohne Revit-Zugriff** laufen, falls auf dem Rechner kein Python installiert ist **[Offen]**.

### 3.2 Praxisfragen zu b) (gelten genauso für a)

| Frage | Antwort |
|---|---|
| **Wie ruft ein Python-Knoten eine Web-Schnittstelle auf?** | Mit `urllib.request` aus der Python-Standardbibliothek. Das ist in Dynamos CPython3 vorhanden, eine Zusatzinstallation ist nicht nötig [Beleg: Prototyp nutzt nur die Standardbibliothek]. |
| **Firmennetz / Proxy** | `urllib` nutzt automatisch die Umgebungsvariable `HTTPS_PROXY`. Welche Proxy-Adresse gilt und ob die Schnittstelle freigegeben ist, klärt die IT (Checkliste). |
| **Zertifikate** | Viele Firmennetze prüfen verschlüsselte Verbindungen mit einem eigenen Stammzertifikat. Dann braucht Python dieses Zertifikat als Datei. Im Prototyp geht das über `KI_CA_DATEI`. Die Prüfung wird **nie abgeschaltet**. |
| **Schlüssel nicht im Skript speichern** | Der Schlüssel steht nur in einer **Windows-Umgebungsvariablen** (`KI_API_KEY`), nie in der `.dyn`-Datei (die enthält den Code im Klartext), nie im Repository, nie in einer Eingabe. Fehlt der Schlüssel, läuft der Prototyp im deutlich gekennzeichneten Testmodus. |
| **Antwortzeit** | Einige Sekunden je Anfrage **[Annahme]**. Deshalb wird je **Kombination** gefragt, nicht je Bauteil, und nicht während des Dynamo-Laufs (a). |
| **Kosten** | Siehe 3.4; gering. |
| **Ausfälle** | Bei vorübergehenden Fehlern (Überlastung, Zeitüberschreitung) bis zu 3 Wiederholungen mit Wartezeit. Danach erhält die Zeile „KI nicht erreichbar“ und Vertrauen NIEDRIG, der lokale Vorschlag bleibt sichtbar. Nichts bricht ab, nichts wird geschrieben. |
| **Ablehnung durch die KI** | Die Schnittstelle kann eine Anfrage aus Sicherheitsgründen ablehnen [Beleg: API-Dokumentation]. Das ist hier unwahrscheinlich, wird aber erkannt: Zeile „abgelehnt“, Mensch entscheidet. Auf der Anthropic-API nutzt der Prototyp zusätzlich die eingebaute Ausweichlösung (`fallbacks: "default"`), die eine abgelehnte Anfrage serverseitig auf einem anderen Modell wiederholt. Über andere Zugänge (z. B. Azure) gibt es diese Funktion nicht; dort fällt sie weg. |
| **Wiederholbarkeit** | (1) Bei den aktuellen Claude-Modellen lässt sich die Zufälligkeit („Temperatur“) **nicht** einstellen, die Schnittstelle lehnt den Parameter ab [Beleg: API-Dokumentation]. (2) Deshalb: **festes Antwortschema**, feste Anweisung mit Versionsnummer, wenig Nachdenkaufwand (`effort: low`) und vor allem ein **Zwischenspeicher**. Jede Antwort wird mit einem Fingerabdruck aus Modell, Anweisung und Eingabe gespeichert. Dieselbe Frage liefert so immer dieselbe Antwort, ohne neue Kosten. (3) In der Tabelle stehen Modell und Anweisungsversion, das Ergebnis ist also dokumentiert. |
| **Die KI darf nichts erfinden** | Die Antwort muss einem **festen Schema** folgen; die Schnittstelle garantiert gültiges Format [Beleg: API-Dokumentation „Structured Outputs“]. Das Feld `wahl` darf nur `K1` bis `K5` oder `KEINE` enthalten (Aufzählung). Die echten LV-Nummern stehen **nicht** in der Auswahl. Das Skript übersetzt K1…K5 selbst in die LV-Position. Eine erfundene Nummer ist damit technisch ausgeschlossen. Zusätzlich prüft das Skript jede Antwort und verwirft Ungültiges. |
| **Welche Daten verlassen den Rechner** | Familie, Typ, Modell, Kommentar, RDS-Funktion und bis zu 5 LV-Kurztexte mit Leistungsnummer. **Keine** Preise, keine Mengen, keine Projektnamen, keine Element-IDs. |

### 3.3 Unsicherheit abbilden

| Stufe | Bedingung (im Prototyp) | Was passiert |
|---|---|---|
| **HOCH** | Regeltreffer, **oder** KI wählt denselben Kandidaten wie der Wortvergleich, Punktzahl ≥ 0,5 und KI-Sicherheit „hoch“ | Vorschlag; Freigabe als Stichprobe |
| **MITTEL** | KI und Wortvergleich stimmen überein, **oder** die KI ist „hoch“ sicher | Mensch prüft |
| **NIEDRIG** | KI wählt KEINE, widerspricht dem Wortvergleich bei geringer Sicherheit, Fehler oder keine Kandidaten | Mensch entscheidet |
| **MEHRDEUTIG** | Produkt steht in mehreren LV-Positionen (Regel) | Mensch wählt die Position |

- Der Vertrauenswert stützt sich **nicht allein** auf die Selbsteinschätzung der KI. Die gilt als schlecht kalibriert **[Annahme]**. Gewertet wird die **Übereinstimmung zweier unabhängiger Verfahren**.
- Die Schwellen sind **[Annahmen]** und werden mit der Messung (Kapitel 4) festgelegt.
- **Nichts wird ohne Bestätigung ins Modell geschrieben.** Die Spalte `Freigabe` füllt ein Mensch mit „ja“, und Dynamo liest nur diese Zeilen. Freigegebene Zeilen wandern in die Datenbank-CSV, damit jede Entscheidung nur einmal fällt.

### 3.4 Kosten (Größenordnung)

| | Annahme / Wert |
|---|---|
| Listenpreise Anthropic, Stand Oktober 2026, je 1 Mio. Token (Eingabe / Ausgabe) [Beleg: Preisliste] | Claude Opus 5.5: 4 $ / 20 $ · Claude Haiku 5.5: 0,10 $ / 0,50 $ |
| Tokens je Kombination [Annahme] | ca. 600 Eingabe + ca. 400 Ausgabe (inkl. kurzem Nachdenken) |
| 200 offene Kombinationen | Opus 5.5: ≈ 0,5 $ + 1,6 $ ≈ **2 $** · Haiku 5.5: **unter 0,10 $** |

Die Kosten entscheiden also nicht. Wiederholte Läufe kosten dank Zwischenspeicher nichts.

**Modellwahl:**
- Der Prototyp nutzt standardmäßig `claude-opus-5-5`. Über `KI_MODELL` ist ein anderes Modell einstellbar.
- Ob ein günstigeres Modell gleich gut zuordnet, lässt sich mit derselben Messung (Kapitel 4) prüfen.
- Die Entscheidung liegt bei dir bzw. der IT, je nachdem, welche Modelle freigegeben sind.

### 3.5 Der Prototyp

Datei: `ki_konzept/ki_zuordnung_prototyp.py`

| Eigenschaft | Umsetzung |
|---|---|
| Eingaben | `2_Kombinationen.csv` (aus der GA-Diagnose) oder eine Datei mit den Spalten `Kategorie;Familie;Typ;Modell;RDS_Funktion;Kommentar`, dazu der SAP-LV-Export (.xlsx) |
| Ausgabe | `uebersetzungstabelle.csv` mit Schlüssel, Freigabe (leer), LV-Position, Quelle, Vertrauen, Begründung und Kandidaten. Im Testmodus heißt die Datei `…_TESTMODUS.csv`. |
| Schlüssel | **nur** aus `KI_API_KEY` bzw. `ANTHROPIC_API_KEY` |
| Testmodus | ohne Schlüssel automatisch; feste Beispielantworten, Quelle „KI-TESTMODUS“ |
| Messung | mit `--referenz referenz.csv` werden Kennzahlen **ohne KI** und **mit KI** nebeneinander ausgegeben |
| Abhängigkeiten | nur Python-Standardbibliothek, also auch in einem Dynamo-Python-Knoten lauffähig |

**Testlauf mit Beispieldaten (Testmodus) [Beleg]:**
- 9 Beispielkombinationen aus dem anonymisierten SAP-LV. Ablauf, Regel, Mehrdeutigkeit, Kandidatenbegrenzung und Zwischenspeicher funktionieren.
- Ohne KI ist der beste Vorschlag bei 8 von 9 Kombinationen richtig. Der Fehler ist der Fall „bis 200 Datenpunkte“.
- Die Kennzahlen „mit KI“ im Testmodus sind **bedeutungslos**, denn die Antworten sind fest vorgegeben. Das Skript weist darauf hin.

---

## 4. Nachweis des Nutzens (Messmethode)

### 4.1 Referenz (Ground Truth)

| Möglichkeit | Bewertung |
|---|---|
| `ZWP_400_LV_Position` lesen | **nicht verwendbar**: in allen 17.835 Elementen leer [Beleg: Diagnose 2]. Außerdem ist es ein Planerparameter, den wir laut Abgrenzung nicht nutzen. |
| **Ausblendversuch (empfohlen)** | Für Bauteile mit gefülltem „Modell“ ist die richtige LV-Position per Regel **sicher bekannt**. Im Versuch werden „Modell“ und die Produktbezeichnung im Typnamen **ausgeblendet**. Dann wird gemessen, ob Wortvergleich bzw. KI die Position aus Familie, Kommentar und RDS-Funktion wiederfinden. Das bildet genau dein Szenario „Modell schlecht gepflegt“ nach und braucht **keine** Handarbeit für die Referenz. In Diagnose 2 sind das rund 40 Siemens-Typen im GA-Bereich [Beleg]; das SAP-LV des Projekts fehlt noch **[Offen]**. |
| Handgeprüfte Stichprobe | Für die übrigen, wirklich unklaren Kombinationen (z. B. Generik-Typen) prüft eine Fachperson eine Zufallsstichprobe von 30–50 **Kombinationen** (2–3 h) **[Annahme]**. Das ist die Kontrolle unter echten Bedingungen. |

### 4.2 Vergleichsgruppen

| Variante | Inhalt |
|---|---|
| V1 | nur Regel (Modell/Typname = Leistungsnummer) |
| V2 | Regel + Wortvergleich (bester lokaler Kandidat), heute `lv_mapping` v2 |
| V3 | Regel + Wortvergleich + KI-Wahl aus den Kandidaten |

### 4.3 Kennzahlen

| Kennzahl | Formel | Aussage |
|---|---|---|
| **Trefferquote** | richtige beste Vorschläge ÷ Kombinationen | Wie oft liegt das Verfahren richtig? |
| **Falschzuordnungen** | falsche Zuordnungen mit Vertrauen HOCH/MITTEL ÷ alle HOCH/MITTEL | Wie gefährlich ist es, dem Vertrauenswert zu folgen? |
| **Prüfquote** | Kombinationen mit NIEDRIG/MEHRDEUTIG ÷ alle | Wie viel Handarbeit bleibt? |
| **Kennlinie** | Trefferquote und Prüfquote für verschiedene Vertrauensschwellen | Wo liegt die beste Schwelle? |
| **Zeitersparnis** | Minuten je 10 Kombinationen: Prüfen **mit** Vorschlag gegen Zuordnen **ohne** Vorschlag | praktischer Nutzen |
| **Kosten** | Tokens × Preis je Lauf, je Kombination | wirtschaftlicher Aufwand |
| **Wiederholbarkeit** | gleiche Antwort in 3 Läufen **ohne** Zwischenspeicher | Streuung der KI; mit Zwischenspeicher per Konstruktion 100 % |
| **Mehrwert der KI** | Kennzahlen V3 − V2 | **Kernaussage der Arbeit** |

**Entscheidungsregel [Annahme, mit dem Betreuer abstimmen]:** Die KI wird empfohlen, wenn V3 gegenüber V2 die Trefferquote um mindestens 10 Prozentpunkte erhöht **oder** die Prüfquote bei gleicher Falschzuordnungsquote um mindestens 10 Prozentpunkte senkt. Sonst lautet das ehrliche Ergebnis „KI nicht nötig“. Auch das ist ein gültiges Ergebnis der Arbeit.

---

## 5. Stufenplan

| Stufe | Inhalt | KI nötig? | Ergebnis |
|---|---|---|---|
| **0** | V1 und V2 auf echten Projektdaten messen: GA-Diagnose (`2_Kombinationen.csv`) + SAP-LV des Projekts + Ausblendversuch | nein | Basiswert ohne KI |
| **1** | IT-Klärung (Checkliste, Kapitel 6) | – | Zugang ja/nein |
| **2** | Prototyp mit echtem Zugang auf denselben Daten → V3; Wiederholbarkeit messen | ja | Mehrwert V3 − V2 |
| **3** | Entscheidung nach der Regel in 4.3 | – | KI ja/nein, begründet |
| **4** | falls ja: Übersetzungstabelle mit Freigabe in den Ablauf von `lv_mapping` v2 übernehmen (Dynamo liest nur freigegebene Zeilen) | ja (einmalig je neuer Kombination) | produktiver Ablauf |
| **5** | optional: Idee 6a (Haupt-/Nebenbauteil) bzw. Idee 3 (Texte für Sonderpositionen) | ja | Zusatznutzen |

---

## 6. Checkliste für die Siemens-IT (zum Weitergeben)

> Betreff: KI-Schnittstelle für eine Bachelorarbeit (Gebäudeautomation, Revit/Dynamo)
>
> Ich schreibe als Werkstudent eine Bachelorarbeit zur systematischen Nachtragserfassung in BIM-Projekten der Gebäudeautomation. Geplant ist, für eine begrenzte Zahl von Bauteiltypen (einige Hundert Anfragen je Projekt) eine KI aus einer vorgegebenen Kandidatenliste die passende Position eines Leistungsverzeichnisses wählen zu lassen. Ein Mensch prüft jedes Ergebnis, bevor es verwendet wird. Dafür bitte ich um Klärung folgender Punkte:
>
> 1. **Freigegebene Dienste:** Welche KI-Dienste mit Programmierschnittstelle (API) sind für Siemens-Mitarbeitende freigegeben (z. B. Anthropic Claude direkt, Claude über Microsoft Azure/Foundry, ein internes KI-Gateway)? Ist Microsoft Copilot per Schnittstelle nutzbar, oder nur im Chat?
> 2. **Zugang:** Wie beantrage ich einen Zugang für ein Studierendenprojekt? Wer muss zustimmen (Vorgesetzte, Datenschutz, Informationssicherheit)?
> 3. **Daten:** Darf ich folgende Daten senden: Revit-Familien- und Typnamen, Herstellerbezeichnungen, Bauteilkommentare, Anlagenkürzel, Leistungsnummern und Kurztexte aus dem SAP-Leistungsverzeichnis, **ohne** Preise, Mengen, Kunden- oder Projektnamen? Welche Einstufung haben diese Daten?
> 4. **Speicherung beim Anbieter:** Werden Anfragen beim Anbieter gespeichert oder zum Training verwendet? Gibt es eine Vereinbarung mit Datenverarbeitung in der EU?
> 5. **Schlüsselverwaltung:** Wie wird der API-Schlüssel ausgegeben und aufbewahrt? Ist eine Windows-Umgebungsvariable zulässig, oder ist ein Tresor bzw. eine Anmeldung über das Firmenkonto vorgeschrieben? Wie oft muss er erneuert werden?
> 6. **Netz:** Welche Adresse (Endpunkt) und welcher Proxy sind zu verwenden? Muss die Adresse freigeschaltet werden? Prüft das Firmennetz verschlüsselte Verbindungen mit einem eigenen Zertifikat, und wo erhalte ich dieses als Datei?
> 7. **Programme:** Darf ich auf meinem Arbeitsrechner ein Python-Skript ausführen, oder nur innerhalb von Autodesk Dynamo (Revit)?
> 8. **Protokollierung:** Gibt es Vorgaben zur Protokollierung der Anfragen (was, wie lange aufbewahren)?
> 9. **Kosten:** Über welche Kostenstelle laufen die Kosten? Gibt es ein Budget- oder Mengenlimit? Erwartet werden wenige Euro je Projekt.
> 10. **Modelle:** Welche Modelle bzw. Versionen sind freigegeben, und darf ich verschiedene zum Vergleich testen?
> 11. **Bachelorarbeit:** Darf ich die Ergebnisse (Kennzahlen, anonymisierte Beispiele) in der Bachelorarbeit veröffentlichen? Gibt es Vorgaben zum Sperrvermerk?
> 12. **Ansprechperson:** Wer ist bei technischen Problemen mit Zugang, Proxy oder Zertifikat ansprechbar?

---

## 7. Annahmen

1. Ein Python-Skript außerhalb von Dynamo kann auf dem Arbeitsrechner laufen. Falls nicht, läuft derselbe Code in einem eigenen Dynamo-Graph.
2. Die Antwortzeit liegt bei einigen Sekunden je Anfrage; die Tokens je Kombination sind wie in 3.4 geschätzt.
3. Die Selbsteinschätzung der KI ist allein nicht verlässlich. Deshalb wird die Übereinstimmung zweier Verfahren gewertet.
4. Die Schwellen für HOCH/MITTEL/NIEDRIG und die Entscheidungsregel (10 Prozentpunkte) sind Vorschläge.
5. Eine KI kann Bedeutungsfälle wie „bis 200 Datenpunkte“ ↔ „< 200 E/A“ lösen. Das ist **nicht gemessen**.
6. Für Siemens-Produkte liefert SAP Kurztexte; Textentwürfe braucht es nur für Sonderleistungen.
7. Rund 40 Siemens-Typen mit gefülltem „Modell“ reichen für einen aussagekräftigen Ausblendversuch. Bei wenigen Typen ist die Statistik schwach und sollte mit einem zweiten Projekt ergänzt werden.

---

## 8. Offene Fragen an dich (nach Wichtigkeit)

| Nr. | Frage | Warum |
|---|---|---|
| **F1** | Kannst du den **SAP-LV-Export dieses Projekts** (.xlsx) bereitstellen? Er bleibt auf deinem Rechner bzw. wird nur lokal ausgewertet. | ohne ihn keine Messung (Stufe 0) |
| **F2** | Gibt es ein **zweites Projekt**, in dem „Modell“ tatsächlich schlecht gepflegt ist? | dort entsteht der echte Nutzen; im aktuellen Projekt ist er klein |
| **F3** | Kann eine Fachperson einmalig 30–50 Kombinationen von Hand zuordnen (2–3 h)? | Referenz für die Generik-Typen |
| **F4** | Darfst du auf dem Arbeitsrechner Python-Skripte außerhalb von Dynamo ausführen? | entscheidet, ob Stufe 2 als Skript oder als Dynamo-Graph läuft |
| **F5** | Möchtest du Idee 6a (Haupt- vs. Nebenbauteil) als zweites KI-Beispiel in der Arbeit? | Umfang der Arbeit |
| **F6** | Ist mit dem Betreuer abgestimmt, dass „KI bringt hier keinen Mehrwert“ ein zulässiges Ergebnis ist? | Ehrlichkeit des Ergebnisses ohne Druck zum KI-Einsatz |
