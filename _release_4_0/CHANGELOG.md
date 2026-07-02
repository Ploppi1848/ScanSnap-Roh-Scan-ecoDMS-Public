# Changelog WebUI 4.0

## Sprint 5F - Supplier Trace

Status: umgesetzt, Auswertung im naechsten Regressionstest

Ziel:

- Lieferantenpipeline transparent machen
- Lieferantenaenderungen mit `SUPPLIER_TRACE` protokollieren
- Ursache falscher Lieferantenwerte vor dem Supplier Guard sichtbar machen

Umsetzung:

- Trace-Schreiber fuer `_debug_text/supplier_trace_<timestamp>.txt`
- Trace bei `safe_set_meta(...)`
- Vorher/Nachher-Trace fuer wichtige Lieferantenphasen
- keine OCR-Volltexte im Trace

Pruefung:

- `python -m py_compile _service\ecodms_scan_service.py` erfolgreich

## Sprint 5E-B - Lieferantenentscheidung Guard

Status: getestet, keine Regressionen, keine messbare Wirkung

Ziel:

- schwache spaete Lieferantengewinner stabilisieren
- Dateinamenfolgefehler durch falsche Lieferanten reduzieren
- echte Telekom-/Amazon-/Amtsgericht-/LVM-/Sparda-Dokumente weiterhin schuetzen

Umsetzung:

- isolierter Schluss-Guard im Scan-Service
- Logging mit `SUPPLIER_GUARD`
- keine Dateinamen-Hartkorrekturen
- keine Referenz- oder Sollwertaenderungen

Pruefung:

- `python -m py_compile _service\ecodms_scan_service.py` erfolgreich

## Sprint 5E-A - Analyse Neuer Dateiname

Status: abgeschlossen

Ziel:

- Analyse der 42 Dokumente mit Abweichung im Feld `Neuer Dateiname`
- Ursachencluster fuer fehlerhafte Dateinamen bilden
- Prioritaeten fuer Sprint 5E-B ableiten

Rahmen:

- keine Codeaenderungen
- keine WebUI-Aenderungen
- keine Refactoring-Arbeiten
- keine Referenz- oder Sollwertaenderungen

## Sprint 5D - Generische Label/Wert-Blockerkennung fuer Nummernfelder

Status: getestet und abgeschlossen

Ziel:

- Generische Erkennung von Label/Wert-Bloecken fuer Nummernfelder
- Fokus auf `RECHNR` und `KUNDENNR`
- Bonprix als Testgruppe, ohne Bonprix-Hartcodierung

Buildvergleich:

- Verbessert: 2 Dokumente
- Verschlechtert: 1 Dokument
- Unveraendert: 117 Dokumente
- Neu auffaellig: 0
- Nicht mehr auffaellig: 8
- `RECHNR` verbessert: 9
- `KUNDENNR` verbessert: 9

Einzige Verschlechterung:

- Lowenstein Medical - Neuer Dateiname

Einordnung:

- Sprint 5D brachte deutliche Feldverbesserungen bei Rechnungsnummer und Kundennummer.
- Es gab keine neu auffaelligen Dokumente.
- Die einzige Regression betrifft den neuen Dateinamen bei Lowenstein Medical und sollte separat bewertet werden.
