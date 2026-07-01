# WebUI 4.0.0-alpha

Build 15

Status: TEST-FREEZE

## Kurzbeschreibung

Diese Version dient als offizieller Alpha-Teststand.

Ab diesem Stand werden grundsaetzlich keine neuen Funktionen mehr in die Alpha aufgenommen.

Zulaessig sind ausschliesslich:

- Fehlerkorrekturen
- Stabilitaetsverbesserungen
- kleine UX-Korrekturen
- offensichtliche Layoutfehler
- Performance-Optimierungen ohne Architekturaenderung

Nicht mehr zulaessig:

- neue Funktionen
- neue Statusmodelle
- groessere UI-Umbauten
- neue Workflows
- neue Architektur

Diese Punkte werden ausschliesslich im LTS-/Beta-Backlog gesammelt.

## Build-15-Highlights

- Statusmodell vereinheitlicht
- Fachliche Schnellpruefung eingefuehrt
- Nachzubearbeiten integriert
- Sonderfaelle integriert
- AKTENZEICHEN ergaenzt
- Dashboard bereinigt
- Qualitaetscenter zur Arbeitsnavigation umgebaut
- Doppelte Kennzahlen entfernt
- Projektcenter-Ruecksprung ergaenzt
- Sollwert-Workflow verbessert
- Technische/Fachliche Status getrennt
- Performance leicht verbessert

## Testmodus

Ab jetzt beginnt die Praxis-Testphase.

Waehrend der Testphase werden gefundene Punkte in drei Kategorien eingeteilt:

### Kritische Fehler

- Absturz
- Datenverlust
- falscher Status
- fehlerhafte Navigation
- fehlerhafte Aufgaben

Sofort beheben.

### UX / Bedienung

- zu viele Klicks
- unklare Bezeichnungen
- fehlende Informationen
- schlechte Navigation
- Layoutprobleme

Sammeln und bewerten.

### Beta / LTS

- Arbeitscenter
- Registerkarten
- Aufgaben direkt in der Schnellpruefung
- PDF-Seiten bearbeiten
- groessere Performance-Umbauten
- Architekturaenderungen

Ausschliesslich ins Backlog aufnehmen.

## Grenzen

Keine Aenderungen an:

- ecodms_scan_service.py
- Outlook-Service
- Dokumentenerkennung
- Statusmodell

Es wird ausschliesslich dokumentiert.

Keine WebUI-Funktionen aendern.

Keine Scan-Service-Dateien aendern.
