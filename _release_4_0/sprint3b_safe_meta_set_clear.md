# Sprint 3B - Safe Meta Set / Clear

## Ziel Sprint 3B

Die Erkennung soll plausible oder bereits korrigierte Werte nicht mehr still durch spaetere Wrapper verschlechtern.

Sprint 3B ist kein Umbau der Erkennungspipeline und keine neue Entscheidungsmaschine. Ziel ist eine erste risikoarme Schutzschicht gegen unbegruendetes Ueberschreiben und pauschales Leeren kritischer Felder.

## Eingefuehrte Schutzlogik

In `_service/ecodms_scan_service.py` wurden zentrale Helfer ergaenzt:

- `safe_set_meta(...)`
- `safe_clear_meta(...)`

Geschuetzte Felder:

- `LIEFERANT`
- `DOKUMENTTYP`
- `RECHNR`
- `KUNDENNR`
- `GESAMTBETRAG`

Prinzipien:

- Leere Werte duerfen plausible vorhandene Werte nicht still ersetzen.
- Pauschales Leeren kritischer Felder wird blockiert, wenn bereits ein plausibler Wert vorhanden ist.
- Ein spaeter `Rechnung`-Fallback darf einen bereits plausiblen Nicht-Rechnungs-Dokumenttyp nicht mehr ueberschreiben.
- Ein spaeter Nicht-Rechnungs-Dokumenttyp darf `Rechnung` weiterhin ersetzen, weil das laut Sprint-3A-Analyse ein haeufiger Folgefehler ist.
- Blockierte Set-/Clear-Versuche werden per Logging nachvollziehbar gemacht.

## Geaenderte Stellen

Die Schutzlogik wurde bewusst nur an zentralen, riskanten Helfern integriert:

- `_clear_invoice_fields_for_non_invoice(...)`
- `_set_580(...)`
- `_clear_nummern_580(...)`
- `_clear_bank_invoice_fields_591(...)`
- `_set_known_593(...)`
- `_clear_invoice_numbers_593(...)`
- `_set_status_5102(...)`
- `_set_lieferant_600(...)`
- `_set_typ_600(...)`

Damit werden vor allem pauschales Nummern-Clearing, dokumenttypbedingtes Leeren und spaete Lieferant-/Dokumenttyp-Setzer abgefangen.

## Betroffene Felder

Direkt betroffen:

- Lieferant
- Dokumenttyp
- RECHNR
- KUNDENNR
- GESAMTBETRAG

Indirekt betroffen:

- Neuer Dateiname, weil dieser aus den finalen Metadaten gebildet wird.

## Risiken

- Einige spaete Wrapper korrigieren tatsaechlich falsche fruehe Werte. Wenn ein frueher Wert plausibel aussieht, kann die Schutzschicht eine spaete Korrektur blockieren.
- Das ist bewusst konservativ und muss mit dem 128er Regressionstest gemessen werden.
- Direkte Einzelfallzuweisungen bleiben vorerst unveraendert, damit keine breite Verhaltensaenderung entsteht.

## Erwarteter Nutzen

- Weniger stille Leerungen von Rechnungsnummer, Kundennummer und Gesamtbetrag.
- Weniger spaete Rueckstufung plausibler Lieferanten.
- Weniger Dominanz des Dokumenttyps `Rechnung`, wenn zuvor bereits ein plausibler Nicht-Rechnungs-Typ erkannt wurde.
- Bessere Nachvollziehbarkeit ueber Logeintraege `SAFE_META`.

## Testhinweise

Empfohlen fuer den naechsten Regressionstest:

- Buildvergleich gegen letzten Snapshot.
- Besondere Kontrolle von Bonprix, Behoerden, Versicherungen, Bank-/Informationsschreiben.
- Pruefen, ob bisherige Verbesserungen durch spaete Spezialwrapper versehentlich blockiert werden.

## Offene Punkte

- Noch kein Kandidatenmodell mit Konfidenzen.
- Noch keine UI fuer Feldfluss-Trace.
- AKTENZEICHEN ist weiterhin als eigenes Service-Metafeld separat zu planen.
- Direkte Einzelfall-Zuweisungen in alten Wrappern sind noch nicht vollstaendig abgeloest.
