# Sprint 2A - Automatische Qualitaetsanalyse

## Ziel

Die WebUI soll die Qualitaetsverbesserung besser unterstuetzen, ohne Erkennungslogik zu aendern.

Grundlage sind ausschliesslich vorhandene Massentest-Ergebnisse und gespeicherte Sollwerte.

## Umgesetzte Funktionen

- Automatische Feldstatistik aus dem Soll/Ist-Vergleich.
- Rangliste der Felder mit den meisten abweichenden Dokumenten.
- Rangliste der Lieferanten mit den meisten Abweichungen.
- Rangliste der Dokumenttypen mit den meisten Abweichungen.
- Top-Dokumente mit den meisten Abweichungen.
- Ampelbewertung pro Dokument:
  - Gruen: keine Abweichungen
  - Gelb: 1 bis 2 Abweichungen
  - Rot: 3 oder mehr Abweichungen
- Prioritaetenliste fuer groessten Qualitaetsgewinn:
  - Ein Feld mit vielen abweichenden Dokumenten hat hohes Verbesserungspotenzial.
- Neue Berichtseite:
  - `/test/massentest/analysis`
- Dokumentenpruefung-Hub verlinkt Berichte / Auswertungen auf die neue Analyse.

## Technische Umsetzung

Neue zentrale Analysefunktionen in `ecodms_webui.py`:

- `massentest_quality_ampel(diff_count)`
- `massentest_quality_snapshot(rows)`
- `massentest_quality_analysis(rows)`
- `massentest_quality_analysis_table(rows, columns, empty)`
- `massentest_quality_analysis_page()`

Die Analyse verwendet bestehende Funktionen:

- `massentest_read_results()`
- `massentest_diff_details(row)`
- `massentest_row_status(row)`
- `MASSTEST_COMPARE`

Es werden keine Massentestdaten geschrieben und keine Sollwerte veraendert.

## Buildvergleich

Sprint 2A implementiert noch keinen echten Buildvergleich.

Vorbereitet wurde eine Snapshot-Struktur:

- Schema: `massentest_quality_snapshot_v1`
- Dokumentstatus je Dokument
- Feldstatus je Dokument
- Feldsummen fuer OK und Abweichung
- App-Version und Erzeugungszeitpunkt

Diese Struktur kann in Sprint 2B genutzt werden, um zwei Builds miteinander zu vergleichen.

## Offene Punkte

- Snapshots als Datei exportieren oder versioniert ablegen.
- Zwei Snapshots miteinander vergleichen.
- Verbesserungen und Regressionen je Dokument automatisch markieren.
- Nur veraenderte/problematische Dokumente als manuelle Pruefliste ausgeben.
- CSV/Markdown-Export der Analyse ergaenzen.

## Vorbereitung fuer Sprint 2B

Empfohlener naechster Schritt:

1. Snapshot des aktuellen Builds speichern.
2. Nach einem neuen Massentest einen zweiten Snapshot erzeugen.
3. Beide Snapshots vergleichen.
4. Veraenderte Dokumente automatisch gruppieren:
   - verbessert
   - verschlechtert
   - unveraendert
   - neu auffaellig

Sprint 2B sollte weiterhin keine Extraktionslogik aendern, sondern zuerst die Buildvergleich-Auswertung fertigstellen.
