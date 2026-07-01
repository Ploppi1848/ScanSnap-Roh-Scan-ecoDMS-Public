# Sprint 2C - Dokumentansicht und PDF-Panning

## Ausgangslage

- Die fachliche Schnellpruefung nutzte bereits ein zweispaltiges Layout.
- Die Abweichungs-/Testergebnisansicht und die normale Sollwertbearbeitung renderten die PDF-Vorschau noch unten unter den Werten.
- PDF-Panning per Maus war nicht zuverlaessig, weil das eingebettete PDF-iframe die Mausereignisse abfing.

## Ersetzte alte Ansichten

- `/test/massentest/result/{row_id}` nutzt jetzt das zweispaltige Review-Layout.
- `/test/massentest/detail/{row_id}` nutzt jetzt ebenfalls PDF links und Soll-/Ist-Bereich rechts.
- `/test/massentest/detail/{row_id}?source=fachlich` verwendet das gemeinsame PDF-Panel.
- `/test/massentest/fachlich/{row_id}` verwendet das gemeinsame PDF-Panel.

## Gemeinsame Dokumentansicht

Ergaenzt wurden zentrale Helfer in `ecodms_webui.py`:

- `massentest_pdf_review_panel_html()`
- `render_document_review()`

Damit werden neue bzw. umgestellte Dokumentansichten einheitlich aufgebaut:

- PDF-Vorschau links
- Status, Soll-/Ist-Pruefung und Entscheidungen rechts
- gleiche Panning-Struktur
- gleiche Ruecksprung-/Aktionsbereiche

## PDF-Panning-Loesung

Das PDF liegt in einem scrollbaren Wrapper:

- Klasse: `qc-pdf-pan-shell`
- Drag-Flaeche: `qc-pdf-pan-capture`
- Cursor: `grab` / `grabbing`
- Scrollleisten bleiben rechts und unten erreichbar.
- Das iframe wird im Wrapper groesser als der sichtbare Bereich gerendert, damit horizontales und vertikales Panning ueber `scrollLeft` und `scrollTop` funktioniert.

## Nachschaerfung Rand / Kalibrierung

- Der horizontale PDF-Scrollbereich wurde erweitert, damit der rechte PDF-Inhalt beim Panning erreichbar bleibt.
- `qc-pdf-pan-shell` verwendet eine stabile Scrollbar-Gasse.
- `qc-pdf-pan-capture` endet vor den Scrollleisten, damit diese weiterhin nutzbar bleiben.
- Das iframe wird breiter und hoeher als der sichtbare Container gerendert:
  - Breite: `calc(140% + 72px)`
  - Hoehe: `calc(126% + 56px)`

## Gepruefte Routen

- `/test/massentest/result/{row_id}`
- `/test/massentest/fachlich/{row_id}`
- `/test/massentest/detail/{row_id}`
- `/test/massentest/detail/{row_id}?source=fachlich`

## Offene Punkte

- Eine spaetere Komponentisierung kann weitere Detailseiten auf `render_document_review()` umstellen.
- Der Browser-PDF-Viewer selbst bleibt ein iframe; eine vollstaendige eigene PDF-Komponente wurde bewusst nicht eingefuehrt.

## Grenzen

- Keine Aenderung an Extraktionslogik.
- Keine Aenderung an Scan-Service oder OCR.
- Keine Aenderung an Referenzdaten oder Massentest-Datenstruktur.
- Keine Aenderung an fachlicher Entscheidungslogik.
