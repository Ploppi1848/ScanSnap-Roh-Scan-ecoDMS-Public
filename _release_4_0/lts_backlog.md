# LTS Backlog

## Fachliche Validierung

### Idee: Schnelle fachliche Dokumentenprüfung

Ziel:
Die fachliche Validierung soll schnell, einfach und reproduzierbar erfolgen.

Beschreibung:
Der Benutzer öffnet ein Dokument und sieht links das PDF.
Rechts werden die erkannten Werte angezeigt:

- Lieferant
- Dokumenttyp
- Dokumentdatum
- Gesamtbetrag
- Neuer Dateiname
- alle weiteren erkannten Felder

Darunter gibt es nur zwei zentrale Aktionen:

- Alles fachlich korrekt
- Sollwerte korrigieren

Nutzen:
Die Prüfung soll pro Dokument möglichst nur 10 bis 20 Sekunden dauern.
Der Benutzer muss nicht zwischen PDF, JSON-Dateien und Listen wechseln.

Status:
Idee / später prüfen

## UX-Überarbeitung: Massentest in Registerkarten

Priorität:
Beta

Ziel:
Die Massentest-Seite soll künftig übersichtlicher werden.

Aktuell werden Technischer Test, Fachliche Validierung und Testverwaltung untereinander dargestellt.

Für die Beta soll geprüft werden, ob diese Bereiche in Registerkarten (Tabs) aufgeteilt werden können.

Vorschlag:

- Technischer Test
- Fachliche Validierung
- Testverwaltung

Ziel:

- deutlich weniger Informationsüberflutung
- jede Arbeitsphase hat ihren eigenen Bereich
- bessere Übersicht
- keine Änderung der Statuslogik

Vor einer Umsetzung soll zunächst ein Architektur- und UI-Konzept erstellt werden.

## Architektur: Gemeinsames Arbeitscenter

Priorität:
Beta

Ziel:
Analysieren, wie Testcenter, Massentest und Projektcenter künftig in einem gemeinsamen Arbeitscenter zusammengeführt werden können.

Dabei soll untersucht werden:

- gemeinsame Navigation
- gemeinsame Aufgabenverwaltung
- gemeinsame Statuslogik
- gemeinsame Filter
- gemeinsame Dokumentansicht
- Wiederverwendung vorhandener Komponenten

Das Arbeitscenter soll langfristig die zentrale Arbeitsoberfläche werden.

Dabei sollen Massentest, Testcenter und Projektcenter nicht mehr als getrennte Anwendungen wirken, sondern unterschiedliche Arbeitsbereiche derselben Oberfläche sein.

Wichtig:

Es soll zunächst ausschließlich eine Architektur- und UI-Analyse erstellt werden.

Keine Umsetzung.

Keine Änderungen an der bestehenden WebUI.

Ergebnis soll ein Konzept für die Beta-Phase sein.

## PDF-Seitenreihenfolge im Prüfworkflow korrigieren

Priorität:
LTS / später prüfen

Ziel:
Bei fachlicher Nacharbeit soll später möglich sein:

- Seitenreihenfolge ändern
- Seiten entfernen
- Seiten drehen
- korrigierte PDF erneut als Referenz speichern

Grund:
Bei Dokumenten mit falscher Seitenreihenfolge ist eine reine Sollwertkorrektur nicht ausreichend.

Status:
Idee / später prüfen

## Aufgabenbearbeitung direkt in der fachlichen Schnellprüfung

Priorität:
Beta / LTS

Ziel:
Bei Fachlicher Nacharbeit soll die zugehörige Aufgabe direkt in der Schnellprüfung sichtbar und bearbeitbar sein:

- Aufgabenstatus
- Notiz
- Aufgabe erledigen
- Nacharbeit erneut prüfen

Damit entfällt später der Wechsel zwischen Qualitätscenter und Projektcenter.

Status:
Idee / später prüfen

## Testcenter und Projektcenter zu gemeinsamem Arbeitscenter zusammenführen

Priorität:
Beta / LTS

Ziel:
Testcenter, Massentest und Projektcenter sollen langfristig nicht mehr wie getrennte Bereiche wirken, sondern als ein gemeinsames Arbeitscenter mit:

- Qualitätssicherung
- Aufgaben
- Einzeltest
- Massentest
- fachlicher Validierung
- Produktivvorbereitung

Grenzen:

- Keine Umsetzung in Alpha
- Keine Scan-Service-Änderungen
- Keine neue Statuslogik
- Keine großen UI-Umbauten
- Erst Analyse/Performance/Korrektur der bestehenden Anzeige

Status:
Idee / später prüfen
