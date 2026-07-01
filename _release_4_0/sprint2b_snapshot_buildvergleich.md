# Sprint 2B - Snapshot und Buildvergleich

## Ziel

Die automatische Qualitaetsanalyse kann den aktuellen Massentest-Stand als separaten Snapshot speichern und zwei gespeicherte Staende miteinander vergleichen.

Es wurden keine Extraktionslogik, OCR, Scan-Service-Dateien, Referenzdaten oder fachliche Entscheidungslogik geaendert.

## Snapshot-Format

Speicherort:

`_massentest/ergebnisse/snapshots/`

Dateiname:

`quality_snapshot_<datum>_<build>.json`

Enthaltene Daten:

- Schema-Version
- App-Version
- Erstellzeitpunkt
- Dokumentanzahl
- Ampelzaehlung
- Dokumentstatus je Dokument
- Anzahl Abweichungen je Dokument
- Feldstatus je Dokument
- Abweichungen je Feld

## Vergleichslogik

Der Buildvergleich vergleicht zwei Snapshots je Dokument und je Feld.

Dokumentbewertung:

- verbessert
- verschlechtert
- unveraendert
- neu auffaellig
- nicht mehr auffaellig

Feldbewertung:

- verbessert: vorher Abweichung, danach ok
- verschlechtert: vorher ok, danach Abweichung
- unveraendert: Feldstatus gleich geblieben

## Bedienung

In der WebUI:

`/test/massentest/analysis`

Dort gibt es jetzt:

- Button `Aktuellen Snapshot speichern`
- Liste vorhandener Snapshots
- Auswahl zweier Snapshots fuer den Buildvergleich
- Ergebnisbereich mit Zusammenfassung, betroffenen Feldern und betroffenen Dokumenten

## Offene Punkte

- Buildvergleich ist aktuell ein Snapshot-zu-Snapshot-Vergleich innerhalb der WebUI.
- Export als Markdown/CSV ist vorbereitet, aber noch nicht umgesetzt.
- Eine automatische Auswahl der "wichtigsten manuell nachzupruefenden Dokumente" kann auf dieser Grundlage in Sprint 2C folgen.

## Vorbereitung fuer Sprint 2C

Sprint 2C kann auf den gespeicherten Snapshots aufbauen:

- Delta-Bericht als Datei erzeugen
- nur Regressionen und stark veraenderte Dokumente als Pruefliste ausgeben
- Feldstatistik historisieren
- Trend je Feld ueber mehrere Builds anzeigen
