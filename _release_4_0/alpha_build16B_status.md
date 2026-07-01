# Alpha Build 16B Status

Version: WebUI 4.0.0-alpha Build 16B
Status: Qualitaetsbuild ausgefuehrt

## Geaenderte Dateien

- `_webservice/ecodms_webui/ecodms_webui.py`
- `_massentest/ergebnisse/massentest_ergebnisse.json` (durch vorhandenen Massentest aktualisiert)
- `_massentest/ergebnisse/massentest_ergebnisse.csv` (durch vorhandenen Massentest aktualisiert)
- `_release_4_0/alpha_build16B_qualitaetsanalyse.md`
- `_release_4_0/alpha_build16B_feldstatistik.csv`
- `_release_4_0/alpha_build16B_vergleich.md`
- `_release_4_0/alpha_build16B_pruefliste.md`
- `_release_4_0/alpha_build16B_status.md`

## Geaenderte Funktionen

- `massentest_postprocess_meta()`
- `massentest_build_new_name()`
- Unterstuetzende interne Hilfsfunktionen fuer Massentest-Normalisierung: `massentest_normalize_supplier_name()`, `massentest_filename_date()`, `massentest_filename_part()`, `massentest_filename_identifier()`

## Anzahl Codeaenderungen

6 gezaehlte Codeaenderungen: 4 Hilfsfunktionen, 1 Anbindung der Lieferanten-Normalisierung, 1 Umstellung der Massentest-Dateinamensbildung.

## Validierung

- WebUI-Datei per `py_compile` geprueft: ohne Syntaxfehler.
- Vorhandener Massentest ueber `/test/massentest/run` ausgefuehrt.
- Vorhandene Soll/Ist-Pruefung ueber `/test/massentest/auto-check` ausgefuehrt.
- Ergebnisdatei enthaelt 128 Dokumente.

## Zusammenfassung

- Lieferantennamen werden im Massentest allgemein von OCR-/Trennzeichenrauschen befreit.
- Dateinamen werden im Massentest aus Datum, Lieferant und einem belastbaren nummerischen Kennzeichen gebildet.
- Lange freie OCR-Texte werden nicht mehr als Dateinamens-Kennzeichen uebernommen.
- Keine Aenderungen an Scan-Service, Outlook-Watcher, Projektcenter, Aufgabenlogik, Statusmodell oder WebUI-Design.

## Empfehlung Build 16C

Build 16C ist sinnvoll, aber getrennt zu planen. Groesste Resthebel liegen in Nummernextraktion, Dokumenttyp-Klassifikation und Gesamtbetrag; diese Bereiche waren ausdruecklich nicht Bestandteil von Build 16B.
