# Build 16 Sprintpaket Start

## Ausgangslage Build 16

Build 16 ist fachlich abgeschlossen.

- Abweichung: 70
- Nachzubearbeiten: 6
- Fachlich validiert: 52
- Offen: 0
- Noch fachlich zu pruefen: 0

Ziel des Sprintpakets ist weniger manuelle Pruefarbeit, eine bessere automatische Abweichungsanalyse und eine praktischere PDF-Bedienung in der fachlichen Pruefung.

## Umgesetzte / angelegte Dateien

- `_release_4_0/build16_regression_abweichungsanalyse.md`
  - Analyse der 70 Abweichungen aus `_massentest/ergebnisse/massentest_ergebnisse.json`
  - Auswertung nach Feld, Lieferant, Dokumenttyp und auffaelligen Mustern
- `_release_4_0/sprint_backlog_webui_extraktion.md`
  - Sprintstruktur fuer fachliche Dokumentansicht, automatische Qualitaetsauswertung und Extraktionsqualitaet
- `_release_4_0/build16_sprintpaket_start.md`
  - Dokumentation dieses Sprintstarts
- `_webservice/ecodms_webui/ecodms_webui.py`
  - PDF-Panning in der fachlichen Schnellpruefung und fachlichen Sollwertbearbeitung

## PDF-Panning

PDF-Panning wurde in der WebUI umgesetzt.

Die PDF-Vorschau liegt weiterhin im vorhandenen iframe, wird aber von einem scrollbaren Wrapper umgeben. Ein transparenter Pan-Bereich nimmt Mausziehen mit gedrueckter linker Maustaste entgegen.

Verhalten:

- Cursor zeigt Hand / Greifen
- Ziehen mit gedrueckter linker Maustaste verschiebt vertikal und horizontal
- Scrollrad bleibt fuer die PDF-Bewegung nutzbar
- keine neue PDF-Komponente
- keine Aenderung an fachlicher Logik

Technischer Hinweis:

Je nach Browser-PDF-Viewer wird zuerst der eingebettete Viewer per `scrollBy()` bewegt. Falls der Browser dies blockiert, scrollt der aeussere PDF-Container als Fallback.

## Keine Aenderungen an Extraktion / Scan-Service

Es wurden keine Aenderungen vorgenommen an:

- Scan-Service
- Outlook-Watcher
- Dokumentenerkennung
- Extraktionslogik
- Statusmodell
- Massentest-Datenstruktur

## Naechste empfohlene Schritte

- Abweichungsanalyse fachlich bewerten
- Sprint 1 priorisieren: alte Abweichungsansicht auf das neue Prueflayout bringen
- Sprint 2 vorbereiten: automatische Build-zu-Build-Qualitaetsauswertung
- Sprint 3 separat planen: Extraktionsqualitaet nur mit Regressionstest auf denselben 128 Referenzen
