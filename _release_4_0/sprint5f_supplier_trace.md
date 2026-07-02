# Sprint 5F - Supplier Trace

## Ziel

Die Lieferantenpipeline soll nachvollziehbar werden.

Ausgangslage:

- Sprint 5E-B war regressionsfrei.
- Buildvergleich: 0 verbessert, 0 verschlechtert, 128 unveraendert.
- Der Supplier Guard greift damit praktisch nicht.
- Die falschen Lieferantenentscheidungen entstehen vermutlich vor dem Guard.

Sprint 5F ist ein Analyse- und Logging-Sprint.

Nicht geaendert:

- keine fachliche Lieferantenentscheidung
- keine Heuristik
- kein Scoring
- keine WebUI
- keine Referenzdaten
- keine Sollwerte
- kein Refactoring

## Pipeline

Die Lieferantenpipeline ist historisch gewachsen und besteht aus mehreren Stufen.

### 1. Konfigurationsbasierte Erkennung

Funktionen:

- `erkenne_lieferant(...)`
- `finde_lieferant_kandidat_bewertet(...)`
- `_lieferant_candidate_score(...)`
- `finde_mapping_wert(...)`

Quelle:

- `lieferanten_konfiguration.txt`
- OCR-Text
- Kopfbereichsgewichtung

Hier entstehen die ersten Lieferantenkandidaten.

Scoring:

- Kopfbereich frueh im Dokument wird hoeher bewertet.
- Rechtsformen und Institutionstypen geben Bonus.
- Bankkontext ohne echten Bankkontext wird abgewertet.
- unplausible Satz-/Empfaenger-/Kontaktzeilen werden abgewertet.

### 2. Basiserkennung und fruehe Bereinigung

Funktionen:

- `erkenne_lieferant_v3(...)`
- `bereinige_lieferant_v552(...)`
- `korrigiere_felder_v54(...)`

Aufgabe:

- bestehende Lieferanten uebernehmen, falls plausibel
- OCR-Muell entfernen
- einige bekannte Shop-/Rechnungsfaelle setzen

### 3. Alt- und Sonderwrapper

Viele spaetere Wrapper koennen den Lieferanten weiterhin setzen oder leeren.

Wichtige Stufen:

- 5.7.x: Einzelkorrekturen, Versicherungen, Justiz, Shops, Satztextbereinigung
- 5.8.x: Erkennungskern, Kontext-/Dateiname-/Briefkopfregeln
- 5.9.x: Restklassifizierung und Lieferantenentscheidung
- 5.10.2: Restfaelle
- 5.11.0: generische Kopfbereichserkennung
- 6.0: Qualitaetsoffensive
- 6.1: Lieferantenoffensive
- 6.5: medizinische Lieferanten
- 6.7: Supplier Guard

### 4. Safe-Meta-Schutz

Funktion:

- `safe_set_meta(...)`

Aufgabe:

- kritische Felder nicht ohne Plausibilitaet ueberschreiben
- spaete schwache Lieferanten blockieren, falls ein plausibler staerkerer Wert vorhanden ist

Grenze:

Nicht alle alten Wrapper verwenden `safe_set_meta(...)`. Einige setzen `meta["LIEFERANT"]` direkt. Deshalb wurde in Sprint 5F zusaetzlich ein Phasen-Trace um die wichtigsten Wrapper gelegt.

### 5. Supplier Guard

Funktion:

- `_apply_supplier_guard_670(...)`

Aufgabe:

- finalen schwachen Lieferanten pruefen
- nur ersetzen, wenn ein staerkerer konfigurierter Kandidat vorhanden ist

Ergebnis aus Regression:

- keine Regressionen
- aber auch keine messbare Wirkung

## Tracepunkte

Marker:

```text
SUPPLIER_TRACE
```

Trace-Ausgabe:

- Python-Logging
- zusaetzlich Datei unter `_debug_text/supplier_trace_<timestamp>.txt`

Es werden keine OCR-Volltexte geschrieben.

Pro Eintrag:

- Verarbeitungsschritt
- bisheriger Lieferant
- neuer Lieferant
- Grund der Aenderung
- Score, falls vorhanden
- Quelle der Entscheidung

Format:

```text
SUPPLIER_TRACE | Schritt: ... | Alt: ... | Neu: ... | Grund: ... | Score: ... | Quelle: ...
```

## Ergaenzte technische Tracepunkte

### `safe_set_meta(...)`

Trace bei Lieferantenaenderung durch:

- leeren oder schwachen Ausgangswert
- normalisierte Variante
- erlaubte Supplier-Decision
- Force-/nicht geschuetztes Feld

Quelle:

- der uebergebene Reason-Text, z. B. `5.9.3 known`, `6.1 Lieferantenoffensive`, `6.7 SUPPLIER_GUARD`

### Phasen-Wrapper

Die folgenden Pipeline-Stufen werden vor/nach Ausfuehrung verglichen:

- `_apply_restklassifizierung_591`
- `_apply_lieferantenentscheidung_593`
- `_apply_restfaelle_5102`
- `_apply_generisch_5110`
- `_apply_quality_600`
- `_apply_lieferantenoffensive_610`
- `_apply_betraege_nummern_630`
- `_apply_stabilisierung_641`
- `_apply_medizinische_lieferanten_650`
- `_apply_supplier_guard_670`

Der Trace wird nur geschrieben, wenn sich `LIEFERANT` zwischen Vorher und Nachher tatsaechlich geaendert hat.

## Reihenfolge der Entscheidungen

Vereinfacht:

1. OCR/Text liegt vor.
2. Konfigurationssuche erzeugt Kandidaten.
3. Kopfbereich und Kontext bewerten Kandidaten.
4. Basisfunktion setzt den ersten Lieferanten.
5. Korrekturwrapper koennen Lieferant normalisieren, ersetzen oder leeren.
6. Safe-Meta schuetzt moderne Setzer vor schwachen Ueberschreibungen.
7. Aeltere Direktsetzer koennen weiterhin ohne Safe-Meta schreiben.
8. Supplier Trace zeigt jetzt, welche Phase den Lieferanten tatsaechlich aendert.
9. Supplier Guard prueft am Ende schwache Gewinner.

## Erwartung fuer den naechsten Regressionstest

Ziel ist nicht bessere Erkennungsqualitaet.

Ziel ist:

- sichtbar machen, wann z. B. Franke zu Amtsgericht wird
- sichtbar machen, wann Lehner zu Telekom wird
- sichtbar machen, wann Bonprix zu Amazon wird
- sichtbar machen, ob der falsche Wert aus Regex, Konfiguration, Fallback oder Direktwrapper kommt

Danach kann Sprint 5G gezielt entscheiden, welche konkrete Pipeline-Stufe fachlich korrigiert werden darf.

## Pruefung

Syntaxpruefung:

```text
python -m py_compile _service\ecodms_scan_service.py
```

Ergebnis: erfolgreich.

## Offene Punkte

- Der Trace ersetzt keine strukturierte Kandidatenliste.
- Direkte Lieferanten-Setzungen ausserhalb der umwickelten Phasen koennen weiterhin nur ueber den naechsten Phasenwechsel sichtbar werden.
- Ein kuenftiger Sprint koennte die Lieferantenpipeline langfristig auf Kandidaten, Score, Quelle und Entscheidung in einem gemeinsamen Modell umbauen.
