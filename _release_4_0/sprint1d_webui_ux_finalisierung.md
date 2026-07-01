# Sprint 1D - WebUI-UX-Finalisierung

## Ziel Sprint 1D

Die WebUI 4.0 soll vor dem nächsten fachlichen Entwicklungsschritt optisch und begrifflich runder wirken.

Schwerpunkt:

- klare Arbeitsbereiche
- ruhigeres Dashboard
- eindeutige Rücksprünge
- weniger alte Begriffe
- zusammengeführte Einstellungen

## Umbenennung Qualität -> Dokumentenprüfung

Der bisherige Hauptbereich `Qualität` wurde sichtbar in `Dokumentenprüfung` umbenannt.

Die Hauptnavigation lautet jetzt:

- Dashboard
- Projekt
- Produktiv
- Dokumentenprüfung
- Einstellungen

## Angepasster Hub

Die Startseite `/test` ist der Hub `Dokumentenprüfung`.

Die Hauptkacheln wurden reduziert auf:

- Einzeldokument
- Massentest
- Berichte / Auswertungen

Regression ist nicht mehr als eigene Hauptkachel sichtbar, sondern in Berichte / Auswertungen eingeordnet.

Referenzen sind nicht mehr als eigene Hauptkachel sichtbar, sondern dem Massentest zugeordnet.

## Ergänzte Rücksprünge

Unterseiten zeigen klarere Rücksprünge:

- Einzeldokument: Zurück zur Dokumentenprüfung
- Massentest: Zurück zur Dokumentenprüfung
- Berichte / Auswertungen: Zurück zur Dokumentenprüfung
- Regressionstest-Zwischenseiten: Zurück zur Dokumentenprüfung

Der Rücksprung aus Berichte / Auswertungen führt nach `/test`.

## Dashboard-Layout

Das Dashboard wurde aufgelockert:

- Produktiv und Test stehen als große Zählerkarten nebeneinander.
- Dokumentenprüfung und Einstellungen stehen darunter ruhiger als Arbeitsbereichskarten.
- Buttons sitzen in den Karten gleichmäßiger am unteren Rand.
- Das Dashboard bleibt reine Anzeige.

## Button-System

Das bestehende Button-Farbsystem wurde weiter vereinheitlicht:

- Speichern / Übernehmen / OK: grün oder Primärfarbe
- Öffnen / Bearbeiten / Navigation: blau oder neutral
- Ignorieren / Nacharbeit: gelb/orange
- Löschen / Gefahr: rot
- Sekundär: weiß/grau mit Rahmen

Es wurden keine neuen Sonderfarben pro Seite eingeführt.

## Einstellungen

Die bisherigen Bereiche Konfiguration und System wurden als Hauptbereich `Einstellungen` zusammengeführt.

Nachschärfung:

- `/config` und `/settings` zeigen dieselbe Einstellungen-Startseite.
- Die Seite ist als Akkordeon aufgebaut.
- Klappzustände werden im Browser per `localStorage` unter `settings_accordion_state` gespeichert.
- Abschnitte:
  - System
  - Ablagekennung & Zähler
  - Weitere Einstellungen
  - Erweiterte Konfigurationsdateien
  - Ordnerstatus

Enthalten/verlinkt:

- Konfigurationsdateien
- Ablagekennung / Zähler
- Ordnerstatus
- Dienste
- Logs
- Wartung
- Lernlisten

Bestehende Routen bleiben erhalten:

- `/config`
- `/ablage`
- `/logs`
- `/learning`
- `/config-form/...`
- `/config/{dateiname}`

Die Textbearbeitung der Konfigurationsdateien ist wieder erreichbar.

## Bewusst nicht geänderte Bereiche

Nicht geändert wurden:

- Extraktionslogik
- Scan-Service-Dateien
- Massentest-Daten
- Referenzdaten
- fachliche Entscheidungslogik
- produktive Aktionen

## Offene Punkte

- Dokumentansichten im nächsten Sprint vereinheitlichen.
- Detailansicht, Schnellprüfung, Sollwertbearbeitung und Abweichungsansicht auf ein gemeinsames Layout bringen.
- Buttonrollen in tiefen Arbeitsansichten weiter bereinigen.
