# Sprint 2B.1 - Snapshotverwaltung

## Ziel

Die Snapshotverwaltung fuer die automatische Qualitaetsanalyse wurde korrigiert, damit jeder Klick auf `Snapshot speichern` eine eigene Datei erzeugt und der Buildvergleich mehrere gespeicherte Staende unterscheiden kann.

## Ursache

Der bisherige Snapshot-Dateiname enthielt Datum und Uhrzeit nur bis Sekunden:

`quality_snapshot_<YYYYMMDD>_<HHMMSS>_<build>.json`

Wenn mehrere Snapshots innerhalb derselben Sekunde erzeugt wurden, konnte dieselbe Datei erneut beschrieben werden. Dadurch war im Buildvergleich trotz mehrerer Speichervorgaenge nur ein Snapshot sichtbar.

## Umsetzung

- Snapshot-Zeitstempel in der Datei enthaelt jetzt Millisekunden.
- Snapshot-Dateiname enthaelt jetzt Mikrosekunden.
- Vor dem Schreiben wird zusaetzlich geprueft, ob der Zielname bereits existiert.
- Falls wider Erwarten eine Kollision entsteht, wird ein laufender Zaehler an den Dateinamen angehaengt.
- Die Snapshotliste liest alle `quality_snapshot_*.json`-Dateien aus `_massentest/ergebnisse/snapshots/` ein.
- Die Liste wird nach dem Speichern ueber Redirect zur Analyse-Seite neu geladen.
- Wenn Basis und Vergleich identisch sind, erscheint der Hinweis:
  `Bitte zwei unterschiedliche Snapshots auswählen.`

## Geaenderte Stellen

Datei:

- `_webservice/ecodms_webui/ecodms_webui.py`

Funktionen:

- `massentest_quality_snapshot()`
- `massentest_quality_snapshot_save()`
- `massentest_quality_snapshot_list()`
- `massentest_quality_analysis_page()`

## Nicht geaendert

- Keine WebUI-Layoutaenderung.
- Keine Erkennungslogik.
- Keine Massentestdatenstruktur.
- Keine Referenzdaten.
- Keine Git-Befehle.

## Pruefung

Nach zweimaligem Speichern muessen mindestens zwei unterschiedliche Snapshot-Dateien im Ordner `_massentest/ergebnisse/snapshots/` vorhanden und im Buildvergleich auswaehlbar sein.
