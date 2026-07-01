# Sprint 1A - WebUI-Grundlayout

## Ziel Sprint 1A

Die WebUI 4.0 soll einen einheitlicheren Grundrahmen bekommen, ohne Fachlogik, Statuslogik oder Datenstrukturen zu veraendern.

Sprint 1A bereitet deshalb nur zentrale UI-Helfer, eine klarere Hauptnavigation und sichtbare Bereichskennzeichnungen vor.

## Umgesetzte Helfer

In `_webservice/ecodms_webui/ecodms_webui.py` wurden vorbereitet:

- `render_navbar()`
  - rendert die Hauptnavigation zentral
  - markiert den aktiven Bereich
  - nutzt nur bestehende Routen
- `render_message_box()`
  - zentraler HTML-Helfer fuer Hinweis-, Erfolgs-, Warn- und Fehlerboxen
  - vorbereitet als kuenftiger Ersatz fuer verstreute `flash`-/`hint`-Bloecke
- `webui_active_nav_key()`
  - ordnet bestehende Seitentitel einem Navigationsbereich zu
- `render_area_badges()`
  - rendert sichtbare Bereichsbadges im Header

## Geaenderte Navigation

Die Hauptnavigation wird jetzt zentral erzeugt und ist fachlich klarer gegliedert:

- Dashboard
- Projektcenter
- Testcenter
- Qualitätscenter
- Produktivcenter
- Konfiguration
- Lernlisten
- Logs
- System / Wartung

Bestehende Routen wurden nicht entfernt.

Zuordnung:

- `Qualitätscenter` verweist auf `/test/massentest`
- `Produktivcenter` verweist auf die bestehende Route `/regression`
- `System / Wartung` verweist auf die bestehende Route `/ablage`

## Eingefuehrte Bereichsbadges

Im globalen Header werden Bereichsbadges zentral vorbereitet und angezeigt.

Aktuell vorgesehen:

- `ALPHA`
- `TEST`
- `PRODUKTIV`
- `Massentest`
- `Regression`

Beispiele:

- Dashboard: `ALPHA`
- Testcenter: `ALPHA`, `TEST`
- Qualitätscenter / Massentest: `ALPHA`, `TEST`, `Massentest`
- Produktivcenter / Regression: `ALPHA`, `PRODUKTIV`, `Regression`

## Bewusst nicht geaenderte Bereiche

Nicht geaendert wurden:

- Dokumentansichten
- fachliche Schnellpruefung
- Sollwertbearbeitung
- Abweichungsansicht
- Massentest-Prueflogik
- Statusmodell
- Massentestdaten
- Aufgabenlogik
- Extraktionslogik
- Scan-Service
- Outlook-Watcher
- bestehende Workflows

## Naechste Schritte fuer Sprint 1B

Sprint 1B sollte die Dokumentansicht vereinheitlichen.

Empfohlene Reihenfolge:

1. `render_pdf_panel()` vorbereiten.
2. Altes PDF-unten-Layout der Abweichungsansicht auf das neue zweispaltige Layout bringen.
3. Fachliche Pruefung, Nacharbeit, Sonderfall und Sollwertbearbeitung visuell angleichen.
4. `render_decision_panel()` fuer Pruefentscheidungen vorbereiten.
5. Statuslogik weiter unveraendert lassen.
