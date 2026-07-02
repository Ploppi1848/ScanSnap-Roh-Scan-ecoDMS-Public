# Sprint 5G - Supplier Candidates

## Ziel

Die Lieferanten-Kandidatenliste soll transparent werden.

Ausgangslage:

- Sprint 5F zeigt, wann ein Lieferant gesetzt oder geaendert wird.
- Es war aber noch nicht sichtbar, welche Kandidaten vorhanden waren und warum ein Kandidat gewann.
- Sprint 5G ergaenzt daher reines Diagnose-Logging.

Nicht geaendert:

- keine Lieferantenentscheidung
- keine Scores
- keine Heuristiken
- keine Guards
- keine WebUI
- keine Referenzdaten
- keine Sollwerte
- kein Refactoring

## Marker

Neuer Marker:

```text
SUPPLIER_CANDIDATES
```

Ausgabe:

```text
_debug_text/supplier_candidates_<timestamp>.txt
```

Die bestehende `SUPPLIER_TRACE`-Datei bleibt unveraendert und zeigt weiterhin nur tatsaechliche Lieferantenaenderungen.

## Protokollierte Informationen

Pro Eintrag:

- Dateiname
- Pipeline-Schritt
- Gewinner des Schritts
- Quelle
- kurzer Grund
- Top-Kandidaten, maximal 10
- Score je Kandidat, falls vorhanden
- Quelle je Kandidat, falls vorhanden

Nicht protokolliert:

- keine OCR-Volltexte
- keine personenbezogenen Volltexte
- keine kompletten Dokumentzeilen

## Ergaenzte Tracepunkte

### `finde_lieferant_kandidat_bewertet(...)`

Hier entsteht die wichtigste strukturierte Kandidatenliste.

Protokolliert:

- Top 10 Kandidaten nach bestehendem Score
- Gewinner nach Score/Kopfnaehe
- Quelle: `Konfiguration/Kopfbereich`
- Suchwort als kurzer Grund

Die bestehende Sortierung und Bewertung wurde nicht veraendert.

### `finde_mapping_wert(...)`

Falls die bewertete Kandidatenliste keinen Gewinner liefert und der einfache Mapping-Fallback greift:

- Gewinner wird als einzelner Kandidat protokolliert
- Quelle: `Konfiguration/Texttreffer`
- Score leer, weil dieser Pfad keinen Score besitzt

### `6.5 Medizinische Lieferanten`

Die medizinische Kopfbereichserkennung protokolliert:

- medizinische Kandidaten
- Score
- Kopfzeilenposition als kurzer Grund
- Gewinner nach medizinischem Score

### Phasen-Fallback aus Sprint 5F

Wenn eine Pipelinephase den Lieferanten aendert, aber keine strukturierte Kandidatenliste verfuegbar ist:

```text
Keine strukturierte Kandidatenliste verfuegbar
```

Das betrifft z. B.:

- 5.9.3 Lieferantenentscheidung
- 5.11.0 Generikerkennung
- 6.0 Qualitaetsoffensive
- 6.1 Lieferantenoffensive
- 6.7 Supplier Guard

Damit wird sichtbar, welcher Schritt einen Gewinner setzt, auch wenn intern keine Kandidatenliste existiert.

## Dateikontext

Ein kleiner Kontext-Wrapper setzt fuer die Dauer von `erzeuge_meta_daten(...)` den aktuellen PDF-Dateinamen.

Dadurch enthalten Kandidateneintraege den Dateinamen, ohne die Fachlogik zu veraendern.

## Auswertung nach dem Massentest

Nach einem Regressionstest:

1. Datei `_debug_text/supplier_candidates_<timestamp>.txt` oeffnen.
2. Nach problematischen Dokumentnamen suchen, z. B.:
   - Franke
   - Lehner
   - Bausparkasse
   - Sparda
   - Bonprix
   - Amazon
   - Telekom
3. Pruefen:
   - War der Soll-Lieferant ueberhaupt Kandidat?
   - Welchen Score hatte er?
   - Welcher falsche Kandidat hatte mehr Score?
   - Kam der Gewinner aus Konfiguration, Kopfbereich, Regex oder Fallback?
   - Wurde spaeter ein unstrukturierter Phasen-Fallback gesetzt?

## Grenzen

- Der Soll-Lieferant ist im Scan-Service nicht direkt bekannt; ob er Kandidat war, muss ueber den Namen in der Kandidatenliste geprueft werden.
- Einige Altregeln haben keine strukturierte Kandidatenliste.
- Der Trace erfasst Diagnoseinformationen, verbessert aber noch keine Erkennungsqualitaet.

## Pruefung

Syntaxpruefung:

```text
python -m py_compile _service\ecodms_scan_service.py
```

Ergebnis: erfolgreich.

## Erwartung fuer den naechsten Test

Der naechste Massentest soll zeigen:

- ob der korrekte Lieferant Kandidat war
- welchen Score er hatte
- welcher falsche Kandidat gewonnen hat
- welcher Pipeline-Schritt den finalen Lieferanten gesetzt hat
