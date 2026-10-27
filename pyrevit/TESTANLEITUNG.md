# Testanleitung Stufe 1 (T1–T10)

## Vorbereitung

1. Testmodell öffnen, in dem `NT_Nachtragsnummer` und `NT_Grund` als
   Exemplarparameter für die GA-Kategorien angelegt sind.
2. Erweiterung installieren (siehe `README.md`) und pyRevit **Reload**
   ausführen.
3. Prüfen, dass der Updater läuft: pyRevit-Ausgabe/Log zeigt keinen Fehler
   „Updater konnte nicht registriert werden“.
4. Zur Kontrolle eine Bauteilliste anlegen, z. B. Kategorie
   *HLS-Bauteile* (bzw. die Kategorie der Fühler), Felder: *Familie und Typ*,
   *ID*, `NT_Nachtragsnummer`, `NT_Grund`. Alternativ jedes Bauteil in der
   Eigenschaften-Palette ansehen.

„Fühler“ steht für ein beliebiges Bauteil einer überwachten GA-Kategorie
(`config.py`).

Unit-Tests ohne Revit (Eingabeprüfung, u. a. T6):
`cd pyrevit && python -m unittest discover tests`

## Testfälle

| Fall | Schritte | Erwartet | Prüfen |
|---|---|---|---|
| **T1** | Button zeigt „Nachtrag starten“ (Modus aus). Einen Fühler platzieren. | Nummer leer, Grund leer | Eigenschaften-Palette bzw. Bauteilliste |
| **T2** | *Nachtrag starten* → Nummer `2`, Grund z. B. `Zusätzliche Raumfühler EG` → Starten. Drei Fühler platzieren. | Button zeigt „Nachtrag 2 aktiv“ (grünes Symbol). Alle drei: Nummer 2, Grund wie eingegeben | Bauteilliste |
| **T3** | Wie T2. Dann *Nachtrag beenden* und einen der drei Fühler kopieren (Strg+C/Strg+V oder *Kopieren*). | Kopie: Nummer leer bzw. 0, Grund leer. Original weiter Nummer 2 | Bauteilliste |
| **T4** | *Nachtrag starten* → Nummer `3`. Einen Fühler aus Nachtrag 2 kopieren. | Kopie: Nummer 3, neuer Grund. Original bleibt 2 | Bauteilliste |
| **T5** | Bei aktivem Nachtrag eine Wand (oder andere nicht überwachte Kategorie) platzieren. | Keine Änderung, kein Hinweis | Wand hat keine NT-Parameter bzw. sie bleiben leer |
| **T6** | *Nachtrag starten* → Nummer `N2` → Starten. Danach `0`, `-1`, `2.0`, leer. | Roter Hinweis im Dialog, Dialog bleibt offen, Zustand unverändert | Button-Beschriftung unverändert |
| **T7** | Einen Fühler löschen. | Sprechblase oben rechts: „Bauteile nicht löschen, sondern als entfallen markieren. Rückgängig mit Strg+Z.“ Kein Dialog, der die Arbeit blockiert | Strg+Z stellt den Fühler wieder her. Andere Bauteile unverändert |
| **T8** | Modell auf einem Rechner ohne pyRevit öffnen (oder: pyRevit → Einstellungen → Erweiterung GA_Nachtrag deaktivieren bzw. Revit ohne pyRevit-Add-in starten), dann Fühler platzieren und speichern. | Beim Öffnen keine Meldung zu einem fehlenden Updater („Dynamic Model Update“), Bearbeiten ohne Fehler | Kein Dialog beim Öffnen |
| **T9** | Projekt **ohne** NT-Parameter öffnen (z. B. neues Projekt aus Vorlage) → *Nachtrag starten*. | Meldung „Parameter fehlen“ mit Liste der fehlenden Parameter. Dialog zur Eingabe erscheint nicht. Button bleibt unverändert | Nichts geschrieben, Strg+Z-Liste leer |
| **T10** | Zentralmodell mit zwei Benutzern: Benutzer B (anderer Revit-Benutzername, Optionen → Allgemein) platziert Fühler ohne Nachtragsmodus und synchronisiert. Benutzer A hat Nachtrag 2 aktiv und führt *Mit Zentralmodell synchronisieren* bzw. *Neueste laden* aus. | Bauteile von B bleiben leer. A kann weiter eigene Bauteile mit Nummer 2 platzieren | Bauteilliste bei A und B |

## Zusätzliche Prüfungen

- **Neustart**: Nachtrag 2 starten, Revit schließen und öffnen. Der Button
  zeigt weiterhin „Nachtrag 2 aktiv“, neue Fühler erhalten Nummer 2.
- **Strg+Z nach Platzieren**: nimmt Bauteil und Kennzeichnung gemeinsam
  zurück.
- **Kategorie ohne Parameterzuordnung**: Ist `NT_Nachtragsnummer` z. B. den
  Sicherheitsgeräten nicht zugeordnet, warnt *Nachtrag starten* vorher. Beim
  Platzieren erscheint einmal pro Projekt eine Sprechblase, dass diese
  Bauteile nicht gekennzeichnet wurden.
- **Worksharing-Prüfung (T2 im Zentralmodell)**: Erscheint beim Platzieren
  die Sprechblase „… nicht verändert, weil sie nicht Ihnen gehören“, bitte
  melden. Dann muss die Besitzprüfung angepasst werden
  (`NUR_EIGENE_BAUTEILE_KENNZEICHNEN` in `config.py`).
