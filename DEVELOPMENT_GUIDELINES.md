# DEVELOPMENT GUIDELINES

## Projektziel

ScanSnap_Roh-Scan-ecoDMS soll eine stabile, nachvollziehbare Arbeitsoberflaeche und Verarbeitungskette fuer Scan-, Test-, Qualitaets- und Produktivablaeufe bereitstellen.

## Git-Workflow

- `main` enthaelt nur stabile, getestete Staende.
- `develop` ist der Entwicklungsbranch.
- Codex fuehrt keine Git-Befehle aus.

## Sprint-Regeln

- Ein Sprint hat genau ein fachliches Ziel.
- Keine Aenderungen ausserhalb des Sprintumfangs.
- Aenderungen werden immer dokumentiert.

## Pruefregeln

- Syntaxpruefung fuer betroffene Python-Dateien durchfuehren.
- Betroffene Seiten, Routen oder Verarbeitungspfade testen.
- Keine Datenaenderung ohne explizite Freigabe.

## Schutzregeln

- Keine Scan-Service- oder Extraktionsaenderung ohne ausdruecklichen Auftrag.
- Referenzdaten nicht ueberschreiben.
- Massentestdatenstruktur nicht aendern.
- Keine produktiven Aktionen aktivieren.

## Dokumentation

- Pro Sprint wird eine Markdown-Datei in `_release_4_0/` angelegt oder aktualisiert.

## Ausgabe Am Ende

- Geaenderte Dateien nennen.
- Durchgefuehrte Pruefung nennen.
- Bewusst nicht geaenderte Bereiche nennen.
- Offene Punkte nennen.
