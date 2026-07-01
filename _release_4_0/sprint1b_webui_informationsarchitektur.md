# Sprint 1B - WebUI-Informationsarchitektur

## Ausgangslage

Die WebUI war funktional gewachsen. Dashboard, Testcenter, Qualitätscenter, Massentest und Produktiv-/Regressionseinstieg zeigten teilweise ähnliche Informationen oder führten in alte Einstiegslogiken.

Ziel von Sprint 1B war eine ruhigere Struktur ohne Änderung an Fachlogik, Statusmodell, Massentestdaten, Referenzen, Dokumentansichten oder Scan-Service.

## Behobener Produktivcenter-Fehler

Der Einstieg `Produktivcenter` führt nicht mehr in die alte Regression-/Freigabeseite mit aktiver Testaktion.

Stattdessen rendert `/regression` jetzt eine sichere Platzhalterseite:

- Titel: Produktivcenter
- Bereichskennzeichnung: PRODUKTIV
- Hinweis: Produktivbereich ist vorbereitet, produktive Aktionen sind noch gesperrt.
- Links zu vorhandenen Bereichen: Qualitätscenter, Einzeldokumenttest, Qualitätsberichte und Regression-Aufgaben

Es wurden keine produktiven Aktionen aktiviert.

## Neue / angepasste Navigationslogik

Die Hauptnavigation ist fachlich klarer geordnet:

- Dashboard
- Projektcenter
- Qualitätscenter
- Produktivcenter
- Konfiguration
- Lernlisten
- Logs
- System / Wartung
- Testcenter

Das Testcenter bleibt erreichbar, wird aber in der Navigation sekundär dargestellt. Qualitätscenter ist der zentrale Einstieg für Tests, Massentest, Referenzen und Qualitätsberichte.

Das Projektcenter wurde sichtbar als Bereich für Aufgaben, Roadmap, Sprintplanung sowie Release- und Buildstände eingeordnet.

## Dashboard-Änderungen

Das Dashboard zeigt nur noch den Betriebsüberblick:

- Scan-Service
- Outlook-Watcher
- Fehlerstatus
- Warteschlange
- Ablagekennung als Anzeige
- nächster Produktiv-Code als Anzeige
- Einstieg ins Qualitätscenter
- Lernlisten-Hinweis

Der technische Ordnerstatus wurde aus dem Dashboard herausgenommen und nach System / Wartung verschoben.

## Ablagekennung / Zähler-Struktur

`/ablage` ist jetzt der Pflegebereich System / Wartung.

Dort gebündelt:

- Bezeichner / Ablagekennung
- Produktiv-Monat
- Produktiv-Jahr
- Produktiv-Zähler
- Produktiv-Vorschau
- Test-Präfix
- Test-Monat
- Test-Jahr
- Test-Zähler
- Test-Vorschau
- Ordnerstatus

Die bestehende Speicherlogik aus `/config-form/box` wird weiterverwendet.

## Qualitätscenter / Massentest-Vereinfachung

Die bisher getrennten Flächen Gesamtübersicht und Fachliche Prüfung wurden auf der Massentest-Seite zu einer gemeinsamen Qualitätscenter-Arbeitsfläche zusammengeführt.

Oben steht der Gesamtstatus:

- Dokumente gesamt
- Technisch bestanden
- Abweichungen
- Offen
- Fachlich validiert
- Noch fachlich zu prüfen
- Nachzubearbeiten
- Sonderfälle

Darunter folgen Arbeitsbereiche:

- Abweichungen bearbeiten
- Noch fachlich prüfen
- Nachzubearbeiten
- Fachlich validiert
- Sonderfälle
- Alle Dokumente

Zusätzlich gibt es kurze Links zu vorhandenen Qualitätswerkzeugen.

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

## Offene Punkte für Sprint 1C

- Alte und neue Dokumentansichten weiter vereinheitlichen.
- Fachliche Prüfung, Abweichungsansicht, Nacharbeit und Sollwertbearbeitung auf gemeinsames Layout bringen.
- Projektcenter, Testcenter, Qualitätscenter und Produktivcenter visuell weiter angleichen.
- Qualitätsberichte und Buildstände später sauberer als eigene Arbeitsbereiche einordnen.
