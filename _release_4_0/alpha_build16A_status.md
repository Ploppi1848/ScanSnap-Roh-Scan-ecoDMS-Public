# Alpha Build 16A Status

Version: WebUI 4.0.0-alpha Build 16A Vorbereitung

Ziel: Analyse- und kleiner Stabilisierungsschritt nach Alpha Build 15.

## Erzeugte Analyse

- Datei: `_release_4_0/alpha_build16A_ursachenanalyse.md`
- Grundlage: `_release_4_0/alpha_build15_qualitaetsanalyse.md`
- Grundlage: `_release_4_0/alpha_build15_feldstatistik.csv`
- Grundlage: `_massentest/ergebnisse/massentest_ergebnisse.json`

Inhalt:

- Top-Problemfelder: Neuer Dateiname, Lieferant, GESAMTBETRAG, RECHNR, KUNDENNR
- Fehlerursachen gruppiert nach Erkennung, Folgefehlern, Normalisierung, Dateinamenslogik, OCR/Textqualitaet und Konfiguration
- Top-20 Korrekturkandidaten fuer Build 16B
- Empfehlung, welche Codebereiche spaeter gezielt geprueft werden sollten

## Kleiner UX-Fix PDF-Bedienung

Geaenderte Datei:

- `_webservice/ecodms_webui/ecodms_webui.py`

Geaenderte CSS-Fundstellen:

- `.qc-fast-pdf` bei Zeile 251
- `.qc-fast-pdf iframe` bei Zeile 252
- `.qc-fast-panel` bei Zeile 253
- `.qc-fast-decision` bei Zeile 254

Umsetzung:

- PDF-Spalte bleibt in der Schnellpruefung sticky im sichtbaren Bereich.
- PDF-Hoehe nutzt jetzt `calc(100vh - 118px)` mit Mindesthoehe.
- Rechte Pruefspalte nutzt dieselbe sichtbare Hoehe und bleibt scrollbar.
- Entscheidungsbereich rechts ist innerhalb der Pruefspalte sticky.
- Keine neuen Buttons.
- Keine Layout-Neuentwicklung.
- Keine fachliche Logikaenderung.
- Keine Aenderung an der Massentest-Datenstruktur.

## Validierung

### Syntax

`ecodms_webui.py` wurde mit Python `py_compile` geprueft.

Ergebnis:

- Kein Syntaxfehler.
- Bekannte alte Warnungen bleiben:
  - invalid escape sequence `\S`
  - invalid escape sequence `\e`

### Fachliche Queue

Gepruefte Fundstellen:

- `massentest_redirect_next_fachlich()` bei Zeile 5485
- Auswahl des naechsten Kandidaten nur mit Bereich `success_pending` bei Zeile 5512
- Nacharbeit wird im Filter `status=offen` ausgeschlossen bei Zeile 4711
- Nacharbeit wird in der Pruefliste als eigener Bereich erkannt bei Zeile 3719

Bewertung:

- Normale fachliche Pruefqueue verwendet weiterhin `success_pending`.
- Nacharbeit bleibt aus `status=offen` ausgeschlossen.
- Automatischer naechster Pruefdatensatz ueberspringt Nacharbeit weiterhin.

### PDF-Bedienung

Bewertung:

- Die PDF-Vorschau bleibt besser im sichtbaren Bereich.
- Der rechte Entscheidungsbereich bleibt beim Scrollen in der Pruefspalte erreichbar.
- Die Aenderung ist bewusst risikoarm und beschraenkt sich auf bestehende CSS-Klassen.

## Nicht geaendert

- Kein Scan-Service geaendert.
- Kein Outlook-Watcher geaendert.
- Keine Erkennungslogik geaendert.
- Keine Statuslogik geaendert.
- Keine neuen Funktionen oder Frameworks.

## Ergebnis

Build 16A ist vorbereitet als Analyse- und kleiner Stabilisierungsschritt.

Build 16B sollte erst nach fachlicher Freigabe gezielt an Erkennungslogik, Lieferanten-Normalisierung, Dateinamensbildung und Nummernfeldern ansetzen.
