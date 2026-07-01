# Sprint 1C - WebUI-Arbeitsbereiche

## Ziel Sprint 1C

Die WebUI soll stärker wie eine Arbeitsoberfläche mit klaren Bereichen wirken:

- weniger gleichwertige Einzelseiten
- klare Trennung von Projekt, Produktiv, Qualität, Konfiguration und System
- Qualitätsbereich als zentraler Einstieg für Test und Prüfung
- Massentest als Unterbereich von Qualität
- Dashboard als reine Anzeige

## Neue Hauptnavigation

Die Hauptnavigation wurde auf wenige Arbeitsbereiche reduziert:

- Dashboard
- Projekt
- Produktiv
- Qualität
- Konfiguration
- System

Bestehende Routen bleiben erhalten. Lernlisten und Logs sind weiterhin erreichbar, aber nicht mehr als eigene Hauptbereiche in der Navigation dargestellt.

## Neue Qualitäts-Hub-Struktur

`/test` ist jetzt die Startseite für den Bereich Qualität.

Die Qualitätsseite enthält Kacheln für:

- Einzeldokument
- Massentest
- Regression
- Referenzen
- Berichte / Auswertungen

Das frühere Testcenter bleibt technisch erreichbar, wird aber logisch als Qualitätsbereich eingeordnet.

## Änderungen an der Massentest-Seite

Die Massentest-Seite wurde als Massentest-Unterbereich entlastet.

Sie zeigt weiterhin:

- Gesamtstatus
- Abweichungen
- fachlich prüfen
- Nacharbeit
- validiert
- Sonderfälle
- alle Dokumente

Prominente Sprünge zu Testcenter, Produktivcenter und weiteren Qualitätswerkzeugen wurden aus der Massentest-Arbeitsfläche entfernt. Der Rückweg führt ruhig zum Qualitäts-Hub.

## Dashboard-Zähler Produktiv / Test

Das Dashboard zeigt jetzt zwei klare Zählerkarten:

- Produktiv
  - aktuelle Produktiv-Ablagekennung
  - nächster Produktiv-Code
  - Produktiv-Zählerstand

- Test
  - Test-Ablage / Test-Präfix
  - nächster Test-Code
  - Test-Zählerstand

Das Dashboard bleibt reine Anzeige. Pflege bleibt im Systembereich.

## Button-Farbsystem

Ein einheitliches Farbsystem wurde im CSS vorbereitet:

- Primär / Speichern / Übernehmen: grün oder Hauptfarbe
- Navigation / Öffnen / Bearbeiten: blau oder neutral
- Warnung / Nacharbeit / Ignorieren: gelb/orange
- Gefahr / Löschen: rot
- Sekundär: weiß/grau mit Rahmen

Bestehende Klassen bleiben kompatibel. Erste sichtbare Standardklassen wurden vereinheitlicht, ohne fachliche Buttons oder Workflows umzubauen.

## Systembereich

`/ablage` ist der gebündelte Systembereich.

Enthalten/verlinkt:

- Wartung
- Ablagekennung / Zähler
- Produktivzähler
- Testzähler
- Ordnerstatus
- Logs
- Dienststatus für Scan-Service und Outlook-Watcher

## Bewusst nicht geänderte Bereiche

Nicht geändert wurden:

- Extraktionslogik
- Scan-Service-Dateien
- Statusberechnung
- Massentest-Datenstruktur
- Referenzdaten
- Dokumentansichten
- fachliche Entscheidungslogik
- produktive Aktionen

## Offene Punkte für Sprint 1D

- Dokumentansichten vereinheitlichen.
- Fachliche Prüfung, Abweichung, Nacharbeit und Sollwertbearbeitung auf gemeinsames Layout bringen.
- Buttonrollen in den Dokumentansichten weiter semantisch angleichen.
- Produktivcenter später fachlich ausarbeiten, ohne produktive Aktionen in Alpha zu aktivieren.
